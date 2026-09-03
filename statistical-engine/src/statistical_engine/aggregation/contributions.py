"""Route contribution calculations for the Airfare Price Index.

Calculates how individual route/segment movements contribute to the aggregate index:
- Level contribution: w_r * I_r,t
- Point contribution: w_r * (I_r,t - I_r,t-1)
- Percentage share of movement: point_contribution / delta_national_index
"""

from __future__ import annotations

from typing import Dict, Optional

from statistical_engine.models.index_result import RouteContribution
from statistical_engine.models.observation import BookingWindow


def calculate_route_contributions(
    route_indices: Dict[str, float],
    weights: Dict[str, float],
    booking_window: BookingWindow,
    previous_route_indices: Optional[Dict[str, float]] = None,
) -> Dict[str, RouteContribution]:
    """Calculate contributions of individual routes to aggregate index level and change.
    
    Args:
        route_indices: Current index values keyed by route (e.g. {'DEL-BOM': 110.0})
        weights: Normalized route weights (e.g. {'DEL-BOM': 0.6})
        booking_window: BookingWindow enum
        previous_route_indices: Optional previous index values to calculate point change contributions
        
    Returns:
        Dict mapping route code to RouteContribution
    """
    contributions: Dict[str, RouteContribution] = {}

    # Calculate aggregate point change if previous indices available
    aggregate_point_change: Optional[float] = None
    if previous_route_indices is not None:
        delta_sum = 0.0
        has_common = False
        for route, curr_idx in route_indices.items():
            if route in previous_route_indices and route in weights:
                prev_idx = previous_route_indices[route]
                w = weights[route]
                delta_sum += w * (curr_idx - prev_idx)
                has_common = True
        if has_common:
            aggregate_point_change = delta_sum

    for route, curr_idx in route_indices.items():
        w = weights.get(route, 0.0)
        level_contrib = w * curr_idx

        point_contrib: Optional[float] = None
        pct_share: Optional[float] = None

        if previous_route_indices is not None and route in previous_route_indices:
            prev_idx = previous_route_indices[route]
            point_contrib = w * (curr_idx - prev_idx)

            if aggregate_point_change is not None and abs(aggregate_point_change) > 1e-6:
                pct_share = (point_contrib / aggregate_point_change) * 100.0

        contributions[route] = RouteContribution(
            route=route,
            booking_window=booking_window,
            weight=w,
            route_index=curr_idx,
            level_contribution=level_contrib,
            point_contribution=point_contrib,
            percentage_share_of_change=pct_share,
        )

    return contributions
