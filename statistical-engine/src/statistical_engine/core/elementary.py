"""Elementary index calculation orchestrating pairing, price relatives and Jevons.

Computes elementary indices for specific (route, booking_window) pairs.
"""

from __future__ import annotations

from typing import List, Optional

from statistical_engine.core.comparability import match_comparable_pairs
from statistical_engine.core.jevons import calculate_jevons_index
from statistical_engine.core.price_relatives import extract_price_relatives
from statistical_engine.models.index_result import (
    CalculationStatus,
    ElementaryIndexResult,
)
from statistical_engine.models.observation import BookingWindow, FareObservation


def calculate_elementary_index_for_slice(
    current_slice: List[FareObservation],
    previous_slice: List[FareObservation],
    route: str,
    booking_window: BookingWindow,
    base_value: float = 100.0,
    min_required_pairs: int = 1,
) -> ElementaryIndexResult:
    """Calculate elementary Jevons index for a given route and booking window slice.
    
    Args:
        current_slice: Current period (t) observations for this route and window.
        previous_slice: Previous period (t-1) observations for this route and window.
        route: Normalized route string (e.g. 'DEL-BOM').
        booking_window: BookingWindow enum.
        base_value: Index base level (default: 100.0).
        min_required_pairs: Minimum matched pairs required to produce a valid index.
        
    Returns:
        ElementaryIndexResult with calculation details.
    """
    pairing_res = match_comparable_pairs(
        current_observations=current_slice,
        previous_observations=previous_slice,
    )
    warnings = list(pairing_res.warnings)

    relatives, rel_warnings = extract_price_relatives(pairing_res.matched_pairs)
    warnings.extend(rel_warnings)

    if len(relatives) < min_required_pairs:
        warnings.append(
            f"Matched pairs count ({len(relatives)}) is less than required minimum ({min_required_pairs})"
        )
        return ElementaryIndexResult(
            route=route,
            booking_window=booking_window,
            index_value=None,
            geometric_mean_relative=None,
            num_matched_pairs=len(relatives),
            num_current_observations=len(current_slice),
            num_previous_observations=len(previous_slice),
            status=CalculationStatus.INSUFFICIENT_DATA,
            warnings=warnings,
        )

    rel_values = [r.relative for r in relatives]
    jevons_res = calculate_jevons_index(rel_values, base_value=base_value)

    if jevons_res.status != CalculationStatus.SUCCESS:
        warnings.append(jevons_res.error_message)
        return ElementaryIndexResult(
            route=route,
            booking_window=booking_window,
            index_value=None,
            geometric_mean_relative=None,
            num_matched_pairs=len(relatives),
            num_current_observations=len(current_slice),
            num_previous_observations=len(previous_slice),
            status=jevons_res.status,
            warnings=warnings,
        )

    return ElementaryIndexResult(
        route=route,
        booking_window=booking_window,
        index_value=jevons_res.index_value,
        geometric_mean_relative=jevons_res.geometric_mean,
        num_matched_pairs=len(relatives),
        num_current_observations=len(current_slice),
        num_previous_observations=len(previous_slice),
        status=CalculationStatus.SUCCESS,
        warnings=warnings,
    )
