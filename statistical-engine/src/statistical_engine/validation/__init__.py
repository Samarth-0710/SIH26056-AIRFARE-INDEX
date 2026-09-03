"""Validation package exports for statistical_engine."""

from statistical_engine.validation.backtest import (
    BacktestRunner,
    generate_demo_test_reference_series,
)
from statistical_engine.validation.metrics import (
    calculate_coverage,
    calculate_directional_accuracy,
    calculate_mae,
    calculate_pearson_correlation,
    calculate_rmse,
    calculate_spearman_correlation,
    calculate_stability,
    compute_all_validation_metrics,
)

__all__ = [
    "BacktestRunner",
    "generate_demo_test_reference_series",
    "calculate_coverage",
    "calculate_directional_accuracy",
    "calculate_mae",
    "calculate_pearson_correlation",
    "calculate_rmse",
    "calculate_spearman_correlation",
    "calculate_stability",
    "compute_all_validation_metrics",
]
