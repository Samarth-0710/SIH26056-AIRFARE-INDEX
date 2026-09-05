"""Chronological orchestration of Statistical Engine daily calculations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

from intelligence.integration.statistical_engine_adapter import (
    StatisticalEngineIntelligenceAdapter,
)
from intelligence.models.result import IntelligenceOutput
from statistical_engine.engine import AirfareStatisticalEngine
from statistical_engine.models.index_result import EngineCalculationOutput
from statistical_engine.models.observation import BookingWindow, FareObservation
from statistical_engine.models.weights import WeightConfig


@dataclass(frozen=True)
class HistoricalDayResult:
    """One successfully executed current/previous observation transition."""

    observation_date: date
    previous_observation_date: date
    engine_output: EngineCalculationOutput
    intelligence_by_window: Dict[BookingWindow, IntelligenceOutput] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class HistoricalOrchestrationResult:
    """Chronological outputs and calculated national series."""

    input_dates: Tuple[date, ...]
    daily_results: Tuple[HistoricalDayResult, ...]
    calculated_series_by_window: Dict[BookingWindow, Dict[date, float]]
    warnings: Tuple[str, ...] = ()

    @property
    def engine_outputs(self) -> Tuple[EngineCalculationOutput, ...]:
        """Return preserved engine outputs in chronological order."""
        return tuple(day.engine_output for day in self.daily_results)


class HistoricalCalculationOrchestrator:
    """Run existing daily engine calculations over ordered observation batches."""

    def __init__(
        self,
        engine: Optional[AirfareStatisticalEngine] = None,
        intelligence_adapter: Optional[StatisticalEngineIntelligenceAdapter] = None,
    ) -> None:
        self.engine = engine or AirfareStatisticalEngine()
        self.intelligence_adapter = (
            intelligence_adapter or StatisticalEngineIntelligenceAdapter()
        )

    def process(
        self,
        observations_by_date: Mapping[date, Sequence[FareObservation]],
        weight_config: Optional[WeightConfig] = None,
        observation_set_version_prefix: str = "OBS_HISTORICAL",
        basket_version: str = "BASKET_v1.0",
        booking_windows: Optional[Sequence[BookingWindow]] = None,
        analyze_intelligence: bool = True,
    ) -> HistoricalOrchestrationResult:
        """Process supplied batches in date order without filling missing dates."""
        if not observations_by_date:
            return HistoricalOrchestrationResult(
                input_dates=(),
                daily_results=(),
                calculated_series_by_window=self._empty_series(booking_windows),
            )

        for observation_date in observations_by_date:
            if not isinstance(observation_date, date):
                raise ValueError(
                    f"Observation date must be a date: {observation_date!r}"
                )

        ordered_dates = tuple(sorted(observations_by_date))
        warnings: List[str] = []
        daily_results: List[HistoricalDayResult] = []
        calculated_series = self._empty_series(booking_windows)
        previous_date: Optional[date] = None
        previous_observations: Optional[Sequence[FareObservation]] = None
        previous_route_indices: Optional[Dict[BookingWindow, Dict[str, float]]] = None

        for current_date in ordered_dates:
            current_observations = observations_by_date[current_date]
            if previous_date is None:
                previous_date = current_date
                previous_observations = current_observations
                continue

            if current_date <= previous_date:
                raise ValueError("Observation dates must be strictly chronological")

            if current_date != previous_date + timedelta(days=1):
                warnings.append(
                    f"Missing historical dates between {previous_date.isoformat()} "
                    f"and {current_date.isoformat()}; no cross-gap calculation created."
                )
                previous_date = current_date
                previous_observations = current_observations
                previous_route_indices = None
                continue

            if previous_observations is None:
                raise ValueError("Previous observations are unavailable for transition")

            engine_output = self.engine.calculate_daily_indices(
                current_observations=list(current_observations),
                previous_observations=list(previous_observations),
                observation_date=current_date,
                previous_observation_date=previous_date,
                weight_config=weight_config,
                observation_set_version=(
                    f"{observation_set_version_prefix}_{current_date.isoformat()}"
                ),
                basket_version=basket_version,
                target_booking_windows=(
                    list(booking_windows) if booking_windows is not None else None
                ),
                previous_route_indices=previous_route_indices,
            )

            intelligence_by_window: Dict[BookingWindow, IntelligenceOutput] = {}
            windows = list(booking_windows) if booking_windows is not None else list(BookingWindow)
            for window in windows:
                national_result = engine_output.national_results.get(window)
                if national_result is not None and national_result.national_index is not None:
                    calculated_series[window][current_date] = national_result.national_index

                if analyze_intelligence and previous_route_indices is not None:
                    intelligence_by_window[window] = self.intelligence_adapter.analyze(
                        engine_output=engine_output,
                        booking_window=window,
                        previous_route_indices=previous_route_indices.get(window, {}),
                    )

            daily_results.append(
                HistoricalDayResult(
                    observation_date=current_date,
                    previous_observation_date=previous_date,
                    engine_output=engine_output,
                    intelligence_by_window=intelligence_by_window,
                )
            )

            previous_route_indices = self._route_indices_by_window(engine_output)
            previous_date = current_date
            previous_observations = current_observations

        return HistoricalOrchestrationResult(
            input_dates=ordered_dates,
            daily_results=tuple(daily_results),
            calculated_series_by_window=calculated_series,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _empty_series(
        booking_windows: Optional[Sequence[BookingWindow]],
    ) -> Dict[BookingWindow, Dict[date, float]]:
        windows = booking_windows if booking_windows is not None else list(BookingWindow)
        return {window: {} for window in windows}

    @staticmethod
    def _route_indices_by_window(
        engine_output: EngineCalculationOutput,
    ) -> Dict[BookingWindow, Dict[str, float]]:
        result: Dict[BookingWindow, Dict[str, float]] = {
            window: {} for window in BookingWindow
        }
        for route, route_result in engine_output.route_results.items():
            for window, index_result in route_result.window_indices.items():
                if index_result.index_value is not None:
                    result.setdefault(window, {})[route] = index_result.index_value
        return result