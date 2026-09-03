"""National aggregate index calculation.

Implements the national aggregation methodology:
    I_t = sum(w_i * I_i,t)
using configured, versioned reference weights.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from statistical_engine.aggregation.contributions import calculate_route_contributions
from statistical_engine.aggregation.weights_manager import (
    calculate_weight_coverage,
    renormalize_weights_for_subbasket,
    validate_weight_config,
)
from statistical_engine.models.index_result import (
    CalculationStatus,
    NationalIndexResult,
    RouteIndexResult,
)
from statistical_engine.models.observation import BookingWindow
from statistical_engine.models.weights import WeightConfig


def calculate_national_index(
    route_results: Dict[str, RouteIndexResult],
    weight_config: WeightConfig,
    booking_window: BookingWindow,
    allow_partial_coverage: bool = False,
    min_coverage_threshold: float = 0.5,
    previous_route_indices: Optional[Dict[str, float]] = None,
) -> NationalIndexResult:
    """Calculate the national aggregate airfare price index for a specific booking window.
    
    Formula:
        I_t = sum_{r in Routes} w_r * I_{r,t}
        
    Args:
        route_results: Mapping of route code to RouteIndexResult
        weight_config: Validated WeightConfig containing route weights
        booking_window: BookingWindow being evaluated
        allow_partial_coverage: Whether to allow computing index on observed subset of basket.
            Defaults to False (strict basket coverage required for authoritative calculation).
            Partial-basket re-normalization is an optional engineering behavior and is NOT an
            asserted official methodology.
        min_coverage_threshold: Minimum coverage ratio required if partial coverage allowed (default: 0.5)
        previous_route_indices: Optional previous index values for contribution tracking
        
    Returns:
        NationalIndexResult with national index level, route contributions, and status.
    """
    warnings: List[str] = []

    # 1. Validate weight configuration
    is_valid_weights, weight_errs = validate_weight_config(weight_config)
    if not is_valid_weights:
        warnings.extend(weight_errs)
        return NationalIndexResult(
            booking_window=booking_window,
            national_index=None,
            route_indices={},
            route_contributions={},
            coverage_ratio=0.0,
            weight_version=weight_config.version,
            status=CalculationStatus.FAILED,
            warnings=warnings,
        )

    # 2. Extract valid route indices for this booking window
    valid_route_indices: Dict[str, float] = {}
    for route, r_res in route_results.items():
        if booking_window in r_res.window_indices:
            w_idx = r_res.window_indices[booking_window]
            if w_idx.status == CalculationStatus.SUCCESS and w_idx.index_value is not None:
                valid_route_indices[route] = w_idx.index_value

    # 3. Check coverage
    coverage_ratio, present_routes, missing_routes = calculate_weight_coverage(
        observed_routes=set(valid_route_indices.keys()),
        weight_config=weight_config,
    )

    if missing_routes:
        warnings.append(
            f"Missing route data for weighted routes: {missing_routes}. Coverage: {coverage_ratio:.2%}"
        )

    # Handle coverage deficiency
    if coverage_ratio == 0.0:
        return NationalIndexResult(
            booking_window=booking_window,
            national_index=None,
            route_indices=valid_route_indices,
            route_contributions={},
            coverage_ratio=0.0,
            weight_version=weight_config.version,
            status=CalculationStatus.INSUFFICIENT_DATA,
            warnings=warnings + ["No observed routes match the weight configuration basket"],
        )

    if not allow_partial_coverage and coverage_ratio < 1.0 - 1e-4:
        return NationalIndexResult(
            booking_window=booking_window,
            national_index=None,
            route_indices=valid_route_indices,
            route_contributions={},
            coverage_ratio=coverage_ratio,
            weight_version=weight_config.version,
            status=CalculationStatus.INSUFFICIENT_DATA,
            warnings=warnings + [
                f"Incomplete route basket under strict authoritative coverage (allow_partial_coverage=False). "
                f"Missing weighted routes: {missing_routes}. Coverage: {coverage_ratio:.2%}"
            ],
        )

    if coverage_ratio < min_coverage_threshold:
        return NationalIndexResult(
            booking_window=booking_window,
            national_index=None,
            route_indices=valid_route_indices,
            route_contributions={},
            coverage_ratio=coverage_ratio,
            weight_version=weight_config.version,
            status=CalculationStatus.INSUFFICIENT_DATA,
            warnings=warnings + [f"Coverage {coverage_ratio:.2%} is below threshold {min_coverage_threshold:.2%}"],
        )

    # 4. Determine effective weights
    if coverage_ratio < 1.0 - 1e-4:
        effective_weights, _ = renormalize_weights_for_subbasket(
            available_routes=set(valid_route_indices.keys()),
            weight_config=weight_config,
        )
        status = CalculationStatus.PARTIAL_COVERAGE
    else:
        effective_weights = {
            r: weight_config.get_weight(r) for r in valid_route_indices.keys()
        }
        status = CalculationStatus.SUCCESS

    # 5. Compute national index: I_t = sum(w_i * I_i,t)
    national_idx = sum(
        effective_weights[r] * valid_route_indices[r]
        for r in valid_route_indices
    )

    # 6. Calculate route contributions
    contributions = calculate_route_contributions(
        route_indices=valid_route_indices,
        weights=effective_weights,
        booking_window=booking_window,
        previous_route_indices=previous_route_indices,
    )

    return NationalIndexResult(
        booking_window=booking_window,
        national_index=national_idx,
        route_indices=valid_route_indices,
        route_contributions=contributions,
        coverage_ratio=coverage_ratio,
        weight_version=weight_config.version,
        status=status,
        warnings=warnings,
    )
