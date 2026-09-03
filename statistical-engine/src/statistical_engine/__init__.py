"""Authoritative Airfare Statistical Index Engine for SIH26056."""

from statistical_engine.engine import (
    ENGINE_METHODOLOGY_VERSION,
    AirfareStatisticalEngine,
)
from statistical_engine.models.index_result import (
    CalculationStatus,
    ElementaryIndexResult,
    EngineCalculationOutput,
    IndexChange,
    NationalIndexResult,
    PriceRelative,
    ReproducibilityMetadata,
    RouteContribution,
    RouteIndexResult,
)
from statistical_engine.models.observation import (
    BookingWindow,
    FareObservation,
    QualityStatus,
)
from statistical_engine.models.validation_result import (
    BacktestResult,
    MetricStatus,
    MetricValue,
    ValidationMetrics,
)
from statistical_engine.models.weights import (
    RouteWeight,
    WeightConfig,
    WeightSource,
    get_demo_reference_weights,
)
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
    "AirfareStatisticalEngine",
    "ENGINE_METHODOLOGY_VERSION",
    "BookingWindow",
    "FareObservation",
    "QualityStatus",
    "RouteWeight",
    "WeightConfig",
    "WeightSource",
    "get_demo_reference_weights",
    "CalculationStatus",
    "ElementaryIndexResult",
    "EngineCalculationOutput",
    "IndexChange",
    "NationalIndexResult",
    "PriceRelative",
    "ReproducibilityMetadata",
    "RouteContribution",
    "RouteIndexResult",
    "BacktestResult",
    "BacktestRunner",
    "generate_demo_test_reference_series",
    "MetricStatus",
    "MetricValue",
    "ValidationMetrics",
    "calculate_coverage",
    "calculate_directional_accuracy",
    "calculate_mae",
    "calculate_pearson_correlation",
    "calculate_rmse",
    "calculate_spearman_correlation",
    "calculate_stability",
    "compute_all_validation_metrics",
]
