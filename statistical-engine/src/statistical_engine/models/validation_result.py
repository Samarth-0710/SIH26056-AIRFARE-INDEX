"""Validation and 30-day back-test result models.

Structured representations for the documented validation metrics:
- Pearson & Spearman Correlation
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- Directional Accuracy
- Coverage
- Stability
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from statistical_engine.models.observation import BookingWindow


class MetricStatus(str, Enum):
    """Status of an individual validation metric calculation."""
    VALID = "VALID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNDEFINED_VARIANCE = "UNDEFINED_VARIANCE"  # Constant series
    MISMATCHED_LENGTH = "MISMATCHED_LENGTH"
    INVALID_SERIES = "INVALID_SERIES"


@dataclass(frozen=True)
class MetricValue:
    """Individual metric calculation with status and diagnostic details."""
    name: str
    value: Optional[float]
    status: MetricStatus
    sample_size: int
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "status": self.status.value,
            "sample_size": self.sample_size,
            "note": self.note,
        }


@dataclass(frozen=True)
class ValidationMetrics:
    """Set of all documented validation metrics for a specific series comparison."""
    pearson_correlation: MetricValue
    spearman_correlation: MetricValue
    mae: MetricValue
    rmse: MetricValue
    directional_accuracy: MetricValue
    coverage: MetricValue
    stability: MetricValue

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pearson_correlation": self.pearson_correlation.to_dict(),
            "spearman_correlation": self.spearman_correlation.to_dict(),
            "mae": self.mae.to_dict(),
            "rmse": self.rmse.to_dict(),
            "directional_accuracy": self.directional_accuracy.to_dict(),
            "coverage": self.coverage.to_dict(),
            "stability": self.stability.to_dict(),
        }


@dataclass(frozen=True)
class BacktestResult:
    """Result of the 30-day back-test against reference data."""
    start_date: date
    end_date: date
    expected_days: int
    matched_days: int
    booking_window_metrics: Dict[BookingWindow, ValidationMetrics]
    reference_source: str
    is_official_reference: bool
    status: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "expected_days": self.expected_days,
            "matched_days": self.matched_days,
            "booking_window_metrics": {
                bw.value: metrics.to_dict()
                for bw, metrics in self.booking_window_metrics.items()
            },
            "reference_source": self.reference_source,
            "is_official_reference": self.is_official_reference,
            "status": self.status,
            "warnings": self.warnings,
        }
