from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median, pstdev
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class FareFeatures:
    """Features derived only from information available at the observation time."""

    route: str
    airline: Optional[str]
    booking_window: str
    source: Optional[str]

    current_fare: Optional[float]
    previous_fare: Optional[float]
    percentage_change: Optional[float]
    rate_of_change: Optional[float]
    acceleration: Optional[float]

    rolling_mean: Optional[float]
    rolling_median: Optional[float]
    rolling_volatility: Optional[float]

    observation_count: int
    source_count: int
    coverage_ratio: Optional[float]
    freshness_hours: Optional[float]

    cross_source_agreement: Optional[float]

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "airline": self.airline,
            "booking_window": self.booking_window,
            "source": self.source,
            "current_fare": self.current_fare,
            "previous_fare": self.previous_fare,
            "percentage_change": self.percentage_change,
            "rate_of_change": self.rate_of_change,
            "acceleration": self.acceleration,
            "rolling_mean": self.rolling_mean,
            "rolling_median": self.rolling_median,
            "rolling_volatility": self.rolling_volatility,
            "observation_count": self.observation_count,
            "source_count": self.source_count,
            "coverage_ratio": self.coverage_ratio,
            "freshness_hours": self.freshness_hours,
            "cross_source_agreement": self.cross_source_agreement,
        }


class FareFeatureEngineer:
    """
    Builds transparent airfare features.

    Historical/rolling features use only the supplied historical values,
    which must represent observations available before or at the current
    observation. The class itself does not fetch future information.

    This component does not calculate the official airfare index.
    """

    def __init__(self, rolling_window: int = 7) -> None:
        if rolling_window < 1:
            raise ValueError("rolling_window must be at least 1")

        self.rolling_window = rolling_window

    @staticmethod
    def _valid_values(values: Iterable[Any]) -> list[float]:
        result = []

        for value in values:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue

            if number > 0:
                result.append(number)

        return result

    @staticmethod
    def _percentage_change(
        current: Optional[float],
        previous: Optional[float],
    ) -> Optional[float]:
        if current is None or previous is None or previous == 0:
            return None

        return ((current - previous) / previous) * 100.0

    @staticmethod
    def _directional_rate(
        percentage_change: Optional[float],
    ) -> Optional[float]:
        if percentage_change is None:
            return None

        return percentage_change

    @staticmethod
    def _acceleration(
        current_change: Optional[float],
        previous_change: Optional[float],
    ) -> Optional[float]:
        if current_change is None or previous_change is None:
            return None

        return current_change - previous_change

    def _rolling_features(
        self,
        historical_fares: Iterable[Any],
    ) -> tuple[
        Optional[float],
        Optional[float],
        Optional[float],
    ]:
        values = self._valid_values(historical_fares)

        if not values:
            return None, None, None

        values = values[-self.rolling_window :]

        return (
            round(mean(values), 2),
            round(median(values), 2),
            round(pstdev(values), 2) if len(values) > 1 else 0.0,
        )

    @staticmethod
    def _source_count(
        current_observations: Optional[Iterable[Any]],
    ) -> int:
        if current_observations is None:
            return 0

        sources = set()

        for observation in current_observations:
            if isinstance(observation, dict):
                source = observation.get("source")
            else:
                source = getattr(observation, "source", None)

            if source is not None and str(source).strip():
                sources.add(str(source).strip())

        return len(sources)

    @staticmethod
    def _observation_count(
        current_observations: Optional[Iterable[Any]],
    ) -> int:
        if current_observations is None:
            return 0

        return sum(1 for _ in current_observations)

    @staticmethod
    def _freshness_hours(
        observation_timestamp: Any,
        reference_timestamp: Any,
    ) -> Optional[float]:
        if observation_timestamp is None or reference_timestamp is None:
            return None

        try:
            if isinstance(observation_timestamp, str):
                observation_timestamp = datetime.fromisoformat(
                    observation_timestamp
                )

            if isinstance(reference_timestamp, str):
                reference_timestamp = datetime.fromisoformat(
                    reference_timestamp
                )

            seconds = (
                reference_timestamp - observation_timestamp
            ).total_seconds()

            return round(max(0.0, seconds) / 3600.0, 2)

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_source_agreement(
        cross_source_result: Any,
    ) -> Optional[float]:
        if cross_source_result is None:
            return None

        if isinstance(cross_source_result, dict):
            value = cross_source_result.get("agreement_ratio")
        else:
            value = getattr(
                cross_source_result,
                "agreement_ratio",
                None,
            )

        if value is None:
            return None

        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return None

    def build(
        self,
        route: str,
        booking_window: str,
        current_fare: Optional[float],
        previous_fare: Optional[float] = None,
        historical_fares: Optional[Iterable[Any]] = None,
        previous_percentage_change: Optional[float] = None,
        airline: Optional[str] = None,
        source: Optional[str] = None,
        current_observations: Optional[Iterable[Any]] = None,
        coverage_ratio: Optional[float] = None,
        cross_source_result: Any = None,
        observation_timestamp: Any = None,
        reference_timestamp: Any = None,
    ) -> FareFeatures:
        """
        Build a feature vector for one route/booking-window observation.

        `historical_fares` must contain only information available up to
        the point being evaluated. The caller is responsible for enforcing
        chronological ordering during back-testing.
        """

        current = None

        if current_fare is not None:
            try:
                value = float(current_fare)
                if value > 0:
                    current = value
            except (TypeError, ValueError):
                pass

        previous = None

        if previous_fare is not None:
            try:
                value = float(previous_fare)
                if value > 0:
                    previous = value
            except (TypeError, ValueError):
                pass

        percentage_change = self._percentage_change(
            current,
            previous,
        )

        rate_of_change = self._directional_rate(
            percentage_change
        )

        acceleration = self._acceleration(
            percentage_change,
            previous_percentage_change,
        )

        rolling_mean = None
        rolling_median = None
        rolling_volatility = None

        if historical_fares is not None:
            (
                rolling_mean,
                rolling_median,
                rolling_volatility,
            ) = self._rolling_features(historical_fares)

        observation_count = self._observation_count(
            current_observations
        )

        source_count = self._source_count(
            current_observations
        )

        freshness_hours = self._freshness_hours(
            observation_timestamp,
            reference_timestamp,
        )

        agreement = self._extract_source_agreement(
            cross_source_result
        )

        return FareFeatures(
            route=route,
            airline=airline,
            booking_window=booking_window,
            source=source,
            current_fare=current,
            previous_fare=previous,
            percentage_change=(
                round(percentage_change, 4)
                if percentage_change is not None
                else None
            ),
            rate_of_change=(
                round(rate_of_change, 4)
                if rate_of_change is not None
                else None
            ),
            acceleration=(
                round(acceleration, 4)
                if acceleration is not None
                else None
            ),
            rolling_mean=rolling_mean,
            rolling_median=rolling_median,
            rolling_volatility=rolling_volatility,
            observation_count=observation_count,
            source_count=source_count,
            coverage_ratio=(
                max(0.0, min(1.0, float(coverage_ratio)))
                if coverage_ratio is not None
                else None
            ),
            freshness_hours=freshness_hours,
            cross_source_agreement=agreement,
        )