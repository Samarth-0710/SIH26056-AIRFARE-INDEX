"""Aggregation package exports for statistical_engine."""

from statistical_engine.aggregation.contributions import (
    calculate_route_contributions,
)
from statistical_engine.aggregation.national_aggregator import (
    calculate_national_index,
)
from statistical_engine.aggregation.route_aggregator import (
    calculate_route_indices,
    group_observations_by_route_and_window,
)
from statistical_engine.aggregation.weights_manager import (
    calculate_weight_coverage,
    renormalize_weights_for_subbasket,
    validate_weight_config,
)

__all__ = [
    "calculate_route_contributions",
    "calculate_national_index",
    "calculate_route_indices",
    "group_observations_by_route_and_window",
    "calculate_weight_coverage",
    "renormalize_weights_for_subbasket",
    "validate_weight_config",
]
