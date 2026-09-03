"""Weights management, validation, and coverage calculation for route aggregation."""

from __future__ import annotations

import math
from typing import Dict, List, Set, Tuple

from statistical_engine.models.weights import WeightConfig


def validate_weight_config(config: WeightConfig) -> Tuple[bool, List[str]]:
    """Validate weight configuration completeness and mathematical correctness."""
    errors: List[str] = []

    if not config.weights:
        errors.append("Weight configuration contains no routes")
        return False, errors

    total_weight = sum(config.weights.values())
    if abs(total_weight - 1.0) > 1e-4:
        errors.append(f"Weights do not sum to 1.0 (actual sum: {total_weight:.6f})")

    for route, w in config.weights.items():
        if w < 0.0:
            errors.append(f"Route '{route}' has negative weight ({w})")
        if math.isnan(w) or math.isinf(w):
            errors.append(f"Route '{route}' has NaN or Infinite weight")

    return len(errors) == 0, errors


def calculate_weight_coverage(
    observed_routes: Set[str],
    weight_config: WeightConfig,
) -> Tuple[float, List[str], List[str]]:
    """Calculate basket weight coverage for a set of observed routes.
    
    Returns:
        coverage_ratio: Total weight sum of routes present in observed_routes (0.0 to 1.0)
        present_routes: List of weighted routes that were observed
        missing_routes: List of weighted routes that were missing in observed routes
    """
    present_routes: List[str] = []
    missing_routes: List[str] = []
    covered_weight = 0.0

    for route, weight in weight_config.weights.items():
        if route in observed_routes:
            present_routes.append(route)
            covered_weight += weight
        else:
            missing_routes.append(route)

    return min(1.0, max(0.0, covered_weight)), present_routes, missing_routes


def renormalize_weights_for_subbasket(
    available_routes: Set[str],
    weight_config: WeightConfig,
) -> Tuple[Dict[str, float], float]:
    """Re-normalize weights for a subset of available routes to sum to 1.0.
    
    Returns:
        renormalized_weights: Mapping of route -> normalized weight
        coverage_ratio: Original coverage proportion
    """
    sub_weights = {
        r: w for r, w in weight_config.weights.items() if r in available_routes and w > 0.0
    }
    total_sub = sum(sub_weights.values())

    if total_sub <= 0.0:
        return {}, 0.0

    renormalized = {r: w / total_sub for r, w in sub_weights.items()}
    return renormalized, total_sub
