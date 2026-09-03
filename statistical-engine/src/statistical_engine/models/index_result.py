"""Output data models for calculated airfare indices and reproducibility metadata.

Structured containers for elementary, route-level, booking-window, and national aggregate indices.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from statistical_engine.models.observation import BookingWindow


class CalculationStatus(str, Enum):
    """Execution status of an index calculation."""
    SUCCESS = "SUCCESS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    FAILED = "FAILED"


@dataclass(frozen=True)
class PriceRelative:
    """Individual price relative P_i,t / P_i,t-1 between two matched comparable observations."""
    fingerprint: str
    route: str
    booking_window: BookingWindow
    current_fare: float
    previous_fare: float
    relative: float

    def __post_init__(self) -> None:
        if self.current_fare <= 0 or self.previous_fare <= 0:
            raise ValueError(
                f"Fares must be positive (> 0), got current={self.current_fare}, prev={self.previous_fare}"
            )
        expected_rel = self.current_fare / self.previous_fare
        if abs(self.relative - expected_rel) > 1e-7:
            raise ValueError(f"Relative mismatch: {self.relative} vs expected {expected_rel}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "route": self.route,
            "booking_window": self.booking_window.value,
            "current_fare": self.current_fare,
            "previous_fare": self.previous_fare,
            "relative": self.relative,
        }


@dataclass(frozen=True)
class ElementaryIndexResult:
    """Result of elementary Jevons calculation for a specific (route, booking_window) segment.
    
    Formula:
        E_t = (product(R_i))^(1/n) * 100
    """
    route: str
    booking_window: BookingWindow
    index_value: Optional[float]
    geometric_mean_relative: Optional[float]
    num_matched_pairs: int
    num_current_observations: int
    num_previous_observations: int
    status: CalculationStatus
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "booking_window": self.booking_window.value,
            "index_value": self.index_value,
            "geometric_mean_relative": self.geometric_mean_relative,
            "num_matched_pairs": self.num_matched_pairs,
            "num_current_observations": self.num_current_observations,
            "num_previous_observations": self.num_previous_observations,
            "status": self.status.value,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class RouteIndexResult:
    """Consolidated route-level index holding separate results for each booking window."""
    route: str
    window_indices: Dict[BookingWindow, ElementaryIndexResult]
    status: CalculationStatus
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "window_indices": {k.value: v.to_dict() for k, v in self.window_indices.items()},
            "status": self.status.value,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class RouteContribution:
    """Movement and point contribution of an individual route to the national index.
    
    Attributes:
        route: Route identifier (e.g. 'DEL-BOM')
        booking_window: Applicable booking window
        weight: Assigned route weight w_r
        route_index: Route index value I_{r,t}
        level_contribution: w_r * I_{r,t}
        point_contribution: w_r * (I_{r,t} - I_{r,t-1}) (optional, when t-1 available)
        percentage_share_of_change: Percentage of total aggregate change attributable to this route
    """
    route: str
    booking_window: BookingWindow
    weight: float
    route_index: float
    level_contribution: float
    point_contribution: Optional[float] = None
    percentage_share_of_change: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "booking_window": self.booking_window.value,
            "weight": self.weight,
            "route_index": self.route_index,
            "level_contribution": self.level_contribution,
            "point_contribution": self.point_contribution,
            "percentage_share_of_change": self.percentage_share_of_change,
        }


@dataclass(frozen=True)
class NationalIndexResult:
    """National aggregate index for a specific booking window.
    
    Formula:
        I_t = sum(w_i * I_i,t)
    """
    booking_window: BookingWindow
    national_index: Optional[float]
    route_indices: Dict[str, float]
    route_contributions: Dict[str, RouteContribution]
    coverage_ratio: float
    weight_version: str
    status: CalculationStatus
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "booking_window": self.booking_window.value,
            "national_index": self.national_index,
            "route_indices": self.route_indices,
            "route_contributions": {k: v.to_dict() for k, v in self.route_contributions.items()},
            "coverage_ratio": self.coverage_ratio,
            "weight_version": self.weight_version,
            "status": self.status.value,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class IndexChange:
    """Calculated change between current and previous index levels."""
    current_index: float
    previous_index: float
    point_change: float
    percentage_change: float

    @classmethod
    def calculate(cls, current: float, previous: float) -> IndexChange:
        if previous == 0.0:
            pct_chg = 0.0
        else:
            pct_chg = ((current - previous) / previous) * 100.0
        return cls(
            current_index=current,
            previous_index=previous,
            point_change=current - previous,
            percentage_change=pct_chg,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_index": self.current_index,
            "previous_index": self.previous_index,
            "point_change": self.point_change,
            "percentage_change": self.percentage_change,
        }


@dataclass(frozen=True)
class ReproducibilityMetadata:
    """Metadata required to guarantee full reproducibility of the calculation."""
    observation_set_version: str
    basket_version: str
    weight_version: str
    methodology_version: str
    calculation_timestamp: datetime
    execution_checksum: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_set_version": self.observation_set_version,
            "basket_version": self.basket_version,
            "weight_version": self.weight_version,
            "methodology_version": self.methodology_version,
            "calculation_timestamp": self.calculation_timestamp.isoformat(),
            "execution_checksum": self.execution_checksum,
        }


@dataclass(frozen=True)
class EngineCalculationOutput:
    """Top-level structured output produced by the Statistical Index Engine."""
    observation_date: date
    previous_observation_date: date
    route_results: Dict[str, RouteIndexResult]
    national_results: Dict[BookingWindow, NationalIndexResult]
    reproducibility: ReproducibilityMetadata
    status: CalculationStatus
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_date": self.observation_date.isoformat(),
            "previous_observation_date": self.previous_observation_date.isoformat(),
            "route_results": {k: v.to_dict() for k, v in self.route_results.items()},
            "national_results": {k.value: v.to_dict() for k, v in self.national_results.items()},
            "reproducibility": self.reproducibility.to_dict(),
            "status": self.status.value,
            "warnings": self.warnings,
        }
