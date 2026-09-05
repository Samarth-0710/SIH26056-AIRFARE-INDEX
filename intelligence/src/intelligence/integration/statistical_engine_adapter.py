"""Adapter from Statistical Engine outputs to the Intelligence orchestrator."""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import date
from typing import Any, Dict, List, Mapping, Optional, Union

from intelligence.models.result import IntelligenceOutput
from intelligence.orchestrator import IntelligenceOrchestrator
from statistical_engine.models.index_result import EngineCalculationOutput
from statistical_engine.models.observation import BookingWindow


class StatisticalEngineIntelligenceAdapter:
    """Translate existing engine results into Intelligence inputs."""

    def __init__(
        self,
        orchestrator: Optional[IntelligenceOrchestrator] = None,
    ) -> None:
        self.orchestrator = orchestrator or IntelligenceOrchestrator()

    def analyze(
        self,
        engine_output: EngineCalculationOutput,
        booking_window: Union[BookingWindow, str] = BookingWindow.T_7,
        previous_route_indices: Optional[Mapping[str, float]] = None,
        **analysis_kwargs: Any,
    ) -> IntelligenceOutput:
        """Analyze one booking window from an existing engine calculation."""
        if engine_output is None:
            raise ValueError("engine_output is required")

        window = self._coerce_booking_window(booking_window)
        current_route_indices: Dict[str, float] = {}
        adapter_warnings: List[str] = []

        for route, route_result in engine_output.route_results.items():
            index_result = route_result.window_indices.get(window)
            if index_result is None:
                adapter_warnings.append(
                    f"[{window.value}] No index result available for route {route}."
                )
                continue

            value = index_result.index_value
            if value is None:
                adapter_warnings.append(
                    f"[{window.value}] Index value unavailable for route {route}."
                )
                continue
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                adapter_warnings.append(
                    f"[{window.value}] Invalid index value skipped for route {route}."
                )
                continue
            current_route_indices[route] = float(value)

        national_result = engine_output.national_results.get(window)
        coverage_ratio = (
            national_result.coverage_ratio if national_result is not None else None
        )
        if national_result is None:
            adapter_warnings.append(
                f"[{window.value}] National result unavailable; coverage is unknown."
            )

        if engine_output.status.value != "SUCCESS":
            adapter_warnings.append(
                f"Statistical Engine status: {engine_output.status.value}."
            )

        result = self.orchestrator.analyze(
            observation_date=engine_output.observation_date.isoformat(),
            current_route_indices=current_route_indices,
            previous_route_indices=dict(previous_route_indices or {}),
            booking_window=window.value,
            coverage_ratio=coverage_ratio,
            **analysis_kwargs,
        )

        warnings = list(result.warnings)
        warnings.extend(engine_output.warnings)
        warnings.extend(adapter_warnings)
        if warnings:
            return replace(result, warnings=warnings)
        return result

    def analyze_windows(
        self,
        engine_output: EngineCalculationOutput,
        booking_windows: Optional[List[Union[BookingWindow, str]]] = None,
        previous_route_indices_by_window: Optional[
            Mapping[Union[BookingWindow, str], Mapping[str, float]]
        ] = None,
    ) -> Dict[BookingWindow, IntelligenceOutput]:
        """Analyze several windows without changing the engine output."""
        windows = booking_windows or list(BookingWindow)
        previous_by_window = previous_route_indices_by_window or {}
        results: Dict[BookingWindow, IntelligenceOutput] = {}

        for requested_window in windows:
            window = self._coerce_booking_window(requested_window)
            previous = previous_by_window.get(window)
            if previous is None:
                previous = previous_by_window.get(window.value)
            results[window] = self.analyze(
                engine_output=engine_output,
                booking_window=window,
                previous_route_indices=previous,
            )

        return results

    @staticmethod
    def _coerce_booking_window(
        booking_window: Union[BookingWindow, str],
    ) -> BookingWindow:
        if isinstance(booking_window, BookingWindow):
            return booking_window
        if isinstance(booking_window, str):
            return BookingWindow.from_string(booking_window)
        raise ValueError(f"Unsupported booking window: {booking_window!r}")