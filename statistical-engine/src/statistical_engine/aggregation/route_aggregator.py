"""Route-level and booking-window index aggregation.

Maintains strictly separate calculations for documented booking windows:
T+1, T+7, T+15, T+30, T+45.
Calculates route-level indices across configurable route observations.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from statistical_engine.core.elementary import calculate_elementary_index_for_slice
from statistical_engine.models.index_result import (
    CalculationStatus,
    ElementaryIndexResult,
    IndexChange,
    RouteIndexResult,
)
from statistical_engine.models.observation import BookingWindow, FareObservation


def group_observations_by_route_and_window(
    observations: List[FareObservation],
) -> Dict[Tuple[str, BookingWindow], List[FareObservation]]:
    """Group observations into slices keyed by (route, booking_window)."""
    grouped: Dict[Tuple[str, BookingWindow], List[FareObservation]] = defaultdict(list)
    for obs in observations:
        grouped[(obs.route, obs.booking_window)].append(obs)
    return grouped


def calculate_route_indices(
    current_observations: List[FareObservation],
    previous_observations: List[FareObservation],
    target_booking_windows: Optional[List[BookingWindow]] = None,
    base_value: float = 100.0,
    min_required_pairs: int = 1,
) -> Dict[str, RouteIndexResult]:
    """Calculate route indices for all routes across each documented booking window.
    
    Args:
        current_observations: Current period observations
        previous_observations: Previous period observations
        target_booking_windows: List of booking windows to compute (defaults to all 5 documented windows)
        base_value: Index base level (default: 100.0)
        min_required_pairs: Minimum matched pairs required per slice
        
    Returns:
        Dict mapping route code (e.g. 'DEL-BOM') to RouteIndexResult.
    """
    if target_booking_windows is None:
        target_booking_windows = [
            BookingWindow.T_1,
            BookingWindow.T_7,
            BookingWindow.T_15,
            BookingWindow.T_30,
            BookingWindow.T_45,
        ]

    curr_grouped = group_observations_by_route_and_window(current_observations)
    prev_grouped = group_observations_by_route_and_window(previous_observations)

    # All unique routes present across either current or previous observations
    all_routes: Set[str] = {k[0] for k in curr_grouped.keys()}.union(
        {k[0] for k in prev_grouped.keys()}
    )

    route_results: Dict[str, RouteIndexResult] = {}

    for route in sorted(list(all_routes)):
        window_results: Dict[BookingWindow, ElementaryIndexResult] = {}
        route_warnings: List[str] = []
        any_success = False

        for bw in target_booking_windows:
            curr_slice = curr_grouped.get((route, bw), [])
            prev_slice = prev_grouped.get((route, bw), [])

            elem_result = calculate_elementary_index_for_slice(
                current_slice=curr_slice,
                previous_slice=prev_slice,
                route=route,
                booking_window=bw,
                base_value=base_value,
                min_required_pairs=min_required_pairs,
            )
            window_results[bw] = elem_result
            if elem_result.status == CalculationStatus.SUCCESS:
                any_success = True
            if elem_result.warnings:
                route_warnings.extend(
                    [f"[{bw.value}] {w}" for w in elem_result.warnings]
                )

        overall_status = (
            CalculationStatus.SUCCESS if any_success else CalculationStatus.INSUFFICIENT_DATA
        )

        route_results[route] = RouteIndexResult(
            route=route,
            window_indices=window_results,
            status=overall_status,
            warnings=route_warnings,
        )

    return route_results
