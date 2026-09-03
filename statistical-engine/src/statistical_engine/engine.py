"""Authoritative Airfare Statistical Index Engine.

Main public entry point and coordinator for:
- Input validation and fingerprinting
- Elementary Jevons short-index calculations
- Route & booking-window index aggregation
- National weighted aggregation
- Route movement & contribution calculations
- Reproducibility provenance metadata tracking
- 30-day back-test validation
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
from typing import Dict, List, Optional, Sequence

from statistical_engine.aggregation.national_aggregator import calculate_national_index
from statistical_engine.aggregation.route_aggregator import calculate_route_indices
from statistical_engine.models.index_result import (
    CalculationStatus,
    EngineCalculationOutput,
    NationalIndexResult,
    ReproducibilityMetadata,
    RouteIndexResult,
)
from statistical_engine.models.observation import BookingWindow, FareObservation
from statistical_engine.models.validation_result import BacktestResult
from statistical_engine.models.weights import WeightConfig, get_demo_reference_weights
from statistical_engine.validation.backtest import BacktestRunner

ENGINE_METHODOLOGY_VERSION = "JEVONS_SHORT_INDEX_v1.0"


class AirfareStatisticalEngine:
    """The authoritative calculator for the SIH26056 Airfare Price Index."""

    def __init__(
        self,
        default_weight_config: Optional[WeightConfig] = None,
        methodology_version: str = ENGINE_METHODOLOGY_VERSION,
        base_value: float = 100.0,
        allow_partial_coverage: bool = False,
        min_coverage_threshold: float = 0.5,
    ) -> None:
        """Initialize the Statistical Engine.
        
        Args:
            default_weight_config: Optional default WeightConfig
            methodology_version: Methodology tag string
            base_value: Base level index (default: 100.0)
            allow_partial_coverage: Whether to allow computing index on observed subset of basket.
                Defaults to False (authoritative strict basket coverage). Partial-basket
                re-normalization is an optional engineering behavior and is NOT an asserted
                official methodology.
            min_coverage_threshold: Minimum coverage ratio required if partial coverage allowed
        """
        self.default_weight_config = default_weight_config
        self.methodology_version = methodology_version
        self.base_value = base_value
        self.allow_partial_coverage = allow_partial_coverage
        self.min_coverage_threshold = min_coverage_threshold

    def calculate_daily_indices(
        self,
        current_observations: List[FareObservation],
        previous_observations: List[FareObservation],
        observation_date: date,
        previous_observation_date: date,
        weight_config: Optional[WeightConfig] = None,
        observation_set_version: str = "OBS_LATEST",
        basket_version: str = "BASKET_v1.0",
        target_booking_windows: Optional[List[BookingWindow]] = None,
        previous_route_indices: Optional[Dict[BookingWindow, Dict[str, float]]] = None,
        allow_partial_coverage: Optional[bool] = None,
    ) -> EngineCalculationOutput:
        """Run complete index calculation for a daily period transition (t-1 -> t).
        
        Args:
            current_observations: Cleaned observations recorded on observation_date
            previous_observations: Cleaned observations recorded on previous_observation_date
            observation_date: Current date t
            previous_observation_date: Previous date t-1
            weight_config: Versioned route weights (uses default or demo if None)
            observation_set_version: Provenance tag for observation dataset
            basket_version: Provenance tag for route basket definition
            target_booking_windows: Booking windows to evaluate (defaults to all 5 documented)
            previous_route_indices: Optional previous route index values for change & point contributions
            allow_partial_coverage: Optional override for basket coverage policy (defaults to engine setting)
            target_booking_windows: Booking windows to evaluate (defaults to all 5 documented)
            previous_route_indices: Optional previous route index values for change & point contributions
            
        Returns:
            Structured EngineCalculationOutput containing route and national indices,
            route contributions, status, and full reproducibility metadata.
        """
        calc_timestamp = datetime.now(timezone.utc)
        warnings: List[str] = []

        active_weights = weight_config or self.default_weight_config
        if active_weights is None:
            warnings.append(
                "No WeightConfig provided. Using DEMO_FIXTURE weights (NOT official DGCA data)."
            )
            active_weights = get_demo_reference_weights()

        if target_booking_windows is None:
            target_booking_windows = [
                BookingWindow.T_1,
                BookingWindow.T_7,
                BookingWindow.T_15,
                BookingWindow.T_30,
                BookingWindow.T_45,
            ]

        # 1. Calculate route-level indices across target booking windows
        route_results = calculate_route_indices(
            current_observations=current_observations,
            previous_observations=previous_observations,
            target_booking_windows=target_booking_windows,
            base_value=self.base_value,
        )

        # 2. Calculate national aggregate indices for each booking window
        national_results: Dict[BookingWindow, NationalIndexResult] = {}
        active_allow_partial = (
            allow_partial_coverage
            if allow_partial_coverage is not None
            else self.allow_partial_coverage
        )
        all_success = True

        for bw in target_booking_windows:
            prev_indices_for_bw = (
                previous_route_indices.get(bw) if previous_route_indices else None
            )
            nat_res = calculate_national_index(
                route_results=route_results,
                weight_config=active_weights,
                booking_window=bw,
                allow_partial_coverage=active_allow_partial,
                min_coverage_threshold=self.min_coverage_threshold,
                previous_route_indices=prev_indices_for_bw,
            )
            national_results[bw] = nat_res
            if nat_res.status != CalculationStatus.SUCCESS and not (
                active_allow_partial and nat_res.status == CalculationStatus.PARTIAL_COVERAGE
            ):
                all_success = False
            if nat_res.warnings:
                warnings.extend([f"[{bw.value}] {w}" for w in nat_res.warnings])

        # 3. Generate deterministic execution checksum for reproducibility
        checksum_payload = {
            "obs_version": observation_set_version,
            "basket_version": basket_version,
            "weight_version": active_weights.version,
            "methodology_version": self.methodology_version,
            "obs_date": observation_date.isoformat(),
            "prev_date": previous_observation_date.isoformat(),
            "curr_obs_count": len(current_observations),
            "prev_obs_count": len(previous_observations),
            "routes_count": len(route_results),
            "national_indices": {
                bw.value: round(res.national_index, 6) if res.national_index is not None else None
                for bw, res in national_results.items()
            },
        }
        checksum_str = hashlib.sha256(
            json.dumps(checksum_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        reproducibility = ReproducibilityMetadata(
            observation_set_version=observation_set_version,
            basket_version=basket_version,
            weight_version=active_weights.version,
            methodology_version=self.methodology_version,
            calculation_timestamp=calc_timestamp,
            execution_checksum=checksum_str,
        )

        overall_status = CalculationStatus.SUCCESS if all_success else CalculationStatus.INSUFFICIENT_DATA

        return EngineCalculationOutput(
            observation_date=observation_date,
            previous_observation_date=previous_observation_date,
            route_results=route_results,
            national_results=national_results,
            reproducibility=reproducibility,
            status=overall_status,
            warnings=warnings,
        )

    def run_backtest(
        self,
        calculated_series_by_window: Dict[BookingWindow, Dict[date, float]],
        backtest_runner: BacktestRunner,
        start_date: date,
        end_date: date,
    ) -> BacktestResult:
        """Run 30-day back-test against reference benchmark data."""
        return backtest_runner.evaluate_window(
            calculated_series_by_window=calculated_series_by_window,
            start_date=start_date,
            end_date=end_date,
        )
