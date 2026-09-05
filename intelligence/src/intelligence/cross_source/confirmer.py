from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Any, Dict, Iterable, List, Optional, Tuple

from intelligence.models.result import (
    CrossSourceConfirmationResult,
    IntelligenceStatus,
)


@dataclass(frozen=True)
class SourceMovement:
    """Movement calculated for one source."""

    source: str
    previous_fare: float
    current_fare: float
    percentage_change: float
    direction: str


class CrossSourceConfirmer:
    """
    Supporting intelligence component that checks whether multiple
    independent fare sources show the same directional movement.

    This component does NOT calculate or modify the official airfare index.
    It provides supporting evidence for movements detected by the
    statistical/intelligence layers.
    """

    def __init__(
        self,
        minimum_sources: int = 2,
        minimum_agreement_ratio: float = 0.5,
        direction_tolerance: float = 0.5,
    ) -> None:
        if minimum_sources < 2:
            raise ValueError("minimum_sources must be at least 2")

        if not 0.0 <= minimum_agreement_ratio <= 1.0:
            raise ValueError(
                "minimum_agreement_ratio must be between 0 and 1"
            )

        if direction_tolerance < 0:
            raise ValueError("direction_tolerance cannot be negative")

        self.minimum_sources = minimum_sources
        self.minimum_agreement_ratio = minimum_agreement_ratio
        self.direction_tolerance = direction_tolerance

    @staticmethod
    def _get_value(observation: Any, field: str) -> Any:
        """Read a field from either an object or dictionary."""
        if isinstance(observation, dict):
            return observation.get(field)

        return getattr(observation, field, None)

    @staticmethod
    def _normalise_source(source: Any) -> Optional[str]:
        if source is None:
            return None

        value = str(source).strip()

        if not value:
            return None

        return value

    @staticmethod
    def _normalise_route(
        origin: Any,
        destination: Any,
    ) -> Optional[str]:
        if origin is None or destination is None:
            return None

        origin_value = str(origin).strip().upper()
        destination_value = str(destination).strip().upper()

        if not origin_value or not destination_value:
            return None

        if origin_value == destination_value:
            return None

        return f"{origin_value}-{destination_value}"

    @staticmethod
    def _normalise_booking_window(value: Any) -> Optional[str]:
        if value is None:
            return None

        if hasattr(value, "value"):
            value = value.value

        value = str(value).strip().upper()

        if not value:
            return None

        return value

    @staticmethod
    def _normalise_date(value: Any) -> Optional[str]:
        if value is None:
            return None

        if isinstance(value, date):
            return value.isoformat()

        value = str(value).strip()

        return value if value else None

    def _group_observations(
        self,
        observations: Iterable[Any],
    ) -> Dict[Tuple[str, str, str, str], List[Any]]:
        """
        Group observations by route, booking window, observation date,
        and source.

        Source remains part of the grouping so that each source contributes
        independently to the confirmation result.
        """
        groups: Dict[
            Tuple[str, str, str, str],
            List[Any],
        ] = defaultdict(list)

        for observation in observations:
            route = self._normalise_route(
                self._get_value(observation, "origin"),
                self._get_value(observation, "destination"),
            )

            booking_window = self._normalise_booking_window(
                self._get_value(observation, "booking_window")
            )

            observation_date = self._normalise_date(
                self._get_value(observation, "observation_date")
            )

            source = self._normalise_source(
                self._get_value(observation, "source")
            )

            comparable_fare = self._get_value(
                observation,
                "comparable_fare",
            )

            if (
                route is None
                or booking_window is None
                or observation_date is None
                or source is None
                or comparable_fare is None
            ):
                continue

            try:
                fare = float(comparable_fare)
            except (TypeError, ValueError):
                continue

            if not isfinite(fare) or fare <= 0:
                continue

            groups[
                (
                    route,
                    booking_window,
                    observation_date,
                    source,
                )
            ].append(observation)

        return groups

    @staticmethod
    def _average_fare(observations: Iterable[Any]) -> Optional[float]:
        fares: List[float] = []

        for observation in observations:
            value = observation.get("comparable_fare") if isinstance(
                observation, dict
            ) else getattr(observation, "comparable_fare", None)

            try:
                fare = float(value)
            except (TypeError, ValueError):
                continue

            if isfinite(fare) and fare > 0:
                fares.append(fare)

        if not fares:
            return None

        return sum(fares) / len(fares)

    def _source_movements(
        self,
        current_observations: Iterable[Any],
        previous_observations: Iterable[Any],
    ) -> Dict[Tuple[str, str, str, str], SourceMovement]:
        current_groups = self._group_observations(current_observations)
        previous_groups = self._group_observations(previous_observations)

        movements: Dict[
            Tuple[str, str, str, str],
            SourceMovement,
        ] = {}

        for key, current_group in current_groups.items():
            previous_group = previous_groups.get(key)

            if not previous_group:
                continue

            current_fare = self._average_fare(current_group)
            previous_fare = self._average_fare(previous_group)

            if current_fare is None or previous_fare is None:
                continue

            if previous_fare == 0:
                continue

            percentage_change = (
                (current_fare - previous_fare)
                / previous_fare
            ) * 100.0

            if abs(percentage_change) <= self.direction_tolerance:
                direction = "STABLE"
            elif percentage_change > 0:
                direction = "UPWARD"
            else:
                direction = "DOWNWARD"

            route, booking_window, observation_date, source = key

            movements[key] = SourceMovement(
                source=source,
                previous_fare=previous_fare,
                current_fare=current_fare,
                percentage_change=percentage_change,
                direction=direction,
            )

        return movements

    def confirm(
        self,
        current_observations: Iterable[Any],
        previous_observations: Iterable[Any],
    ) -> List[CrossSourceConfirmationResult]:
        """
        Produce cross-source confirmation results.

        Current and previous observations should contain normalized fare
        observations from the Data Quality layer.

        Results are generated separately for each route, booking window,
        and observation date.
        """
        movements = self._source_movements(
            current_observations,
            previous_observations,
        )

        if not movements:
            return []

        grouped: Dict[
            Tuple[str, str, str],
            List[SourceMovement],
        ] = defaultdict(list)

        for key, movement in movements.items():
            route, booking_window, observation_date, _source = key

            grouped[
                (route, booking_window, observation_date)
            ].append(movement)

        results: List[CrossSourceConfirmationResult] = []

        for (
            route,
            booking_window,
            observation_date,
        ), source_movements in sorted(grouped.items()):
            sources = sorted(
                movement.source
                for movement in source_movements
            )

            source_count = len(sources)

            if source_count < self.minimum_sources:
                results.append(
                    CrossSourceConfirmationResult(
                        route=route,
                        booking_window=booking_window,
                        observation_date=observation_date,
                        sources=sources,
                        source_count=source_count,
                        agreeing_sources=[],
                        agreement_ratio=None,
                        direction=None,
                        confirmed=False,
                        strength="INSUFFICIENT",
                        reason=(
                            "Insufficient independent sources for "
                            "cross-source confirmation."
                        ),
                        status=IntelligenceStatus.INSUFFICIENT_DATA,
                        warnings=[
                            "At least two independent sources are required."
                        ],
                    )
                )
                continue

            upward = [
                movement
                for movement in source_movements
                if movement.direction == "UPWARD"
            ]

            downward = [
                movement
                for movement in source_movements
                if movement.direction == "DOWNWARD"
            ]

            stable = [
                movement
                for movement in source_movements
                if movement.direction == "STABLE"
            ]

            directional_groups = {
                "UPWARD": upward,
                "DOWNWARD": downward,
                "STABLE": stable,
            }

            direction, agreeing_movements = max(
                directional_groups.items(),
                key=lambda item: len(item[1]),
            )

            agreement_ratio = (
                len(agreeing_movements) / source_count
            )

            confirmed = (
                len(agreeing_movements) >= self.minimum_sources
                and agreement_ratio >= self.minimum_agreement_ratio
                and direction != "STABLE"
            )

            agreeing_sources = sorted(
                movement.source
                for movement in agreeing_movements
            )

            if not confirmed:
                strength = "WEAK"
                reason = (
                    "Sources do not provide sufficient directional "
                    "agreement for confirmation."
                )
            elif agreement_ratio >= 0.75:
                strength = "STRONG"
                reason = (
                    f"{len(agreeing_sources)} of {source_count} sources "
                    f"support a {direction.lower()} movement."
                )
            else:
                strength = "MODERATE"
                reason = (
                    f"{len(agreeing_sources)} of {source_count} sources "
                    f"support a {direction.lower()} movement."
                )

            results.append(
                CrossSourceConfirmationResult(
                    route=route,
                    booking_window=booking_window,
                    observation_date=observation_date,
                    sources=sources,
                    source_count=source_count,
                    agreeing_sources=agreeing_sources,
                    agreement_ratio=agreement_ratio,
                    direction=direction,
                    confirmed=confirmed,
                    strength=strength,
                    reason=reason,
                    status=IntelligenceStatus.SUCCESS,
                )
            )

        return results