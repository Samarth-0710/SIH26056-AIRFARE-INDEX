from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ConfidenceSupportResult:
    """Supporting confidence signal for an intelligence result.

    This is NOT a statistical confidence interval and does not
    modify the official airfare index.
    """

    route: str
    booking_window: str
    confidence_score: Optional[float]
    confidence_level: str

    coverage_ratio: Optional[float]
    cross_source_agreement: Optional[float]
    anomaly_available: bool

    source_coverage: Optional[float]
    observation_count: Optional[int]
    expected_observation_count: Optional[int]
    observation_volume_ratio: Optional[float]

    data_quality: Optional[float]
    freshness_hours: Optional[float]

    reason: str

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "booking_window": self.booking_window,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "coverage_ratio": self.coverage_ratio,
            "cross_source_agreement": self.cross_source_agreement,
            "anomaly_available": self.anomaly_available,
            "source_coverage": self.source_coverage,
            "observation_count": self.observation_count,
            "expected_observation_count": (
                self.expected_observation_count
            ),
            "observation_volume_ratio": (
                self.observation_volume_ratio
            ),
            "data_quality": self.data_quality,
            "freshness_hours": self.freshness_hours,
            "reason": self.reason,
        }


class ConfidenceSupportScorer:
    """
    Produces an interpretable 0-100 supporting confidence score.

    Signals:
      - route/data coverage
      - source coverage
      - observation volume
      - cross-source agreement
      - data quality
      - freshness
      - availability of anomaly evidence

    This score is an Intelligence-layer diagnostic signal.

    It is NOT an official statistical confidence measure,
    confidence interval, or CPI calculation.

    The default weights are analytical implementation choices.
    They are not official statistical weights.
    """

    def __init__(
        self,
        coverage_weight: float = 0.25,
        source_coverage_weight: float = 0.10,
        observation_volume_weight: float = 0.15,
        agreement_weight: float = 0.20,
        data_quality_weight: float = 0.15,
        freshness_weight: float = 0.10,
        anomaly_weight: float = 0.05,
        maximum_freshness_hours: float = 48.0,
    ) -> None:

        if maximum_freshness_hours <= 0:
            raise ValueError(
                "maximum_freshness_hours must be positive."
            )

        weights = {
            "coverage": coverage_weight,
            "source_coverage": source_coverage_weight,
            "observation_volume": observation_volume_weight,
            "agreement": agreement_weight,
            "data_quality": data_quality_weight,
            "freshness": freshness_weight,
            "anomaly": anomaly_weight,
        }

        if any(weight < 0 for weight in weights.values()):
            raise ValueError(
                "Weights cannot be negative."
            )

        total = sum(weights.values())

        if total <= 0:
            raise ValueError(
                "At least one weight must be positive."
            )

        self.coverage_weight = (
            coverage_weight / total
        )

        self.source_coverage_weight = (
            source_coverage_weight / total
        )

        self.observation_volume_weight = (
            observation_volume_weight / total
        )

        self.agreement_weight = (
            agreement_weight / total
        )

        self.data_quality_weight = (
            data_quality_weight / total
        )

        self.freshness_weight = (
            freshness_weight / total
        )

        self.anomaly_weight = (
            anomaly_weight / total
        )

        self.maximum_freshness_hours = (
            float(maximum_freshness_hours)
        )

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 100.0,
    ) -> float:
        return max(
            minimum,
            min(maximum, value),
        )

    @staticmethod
    def _ratio_signal(
        ratio: Optional[float],
    ) -> float:
        """
        Convert a normalized 0-1 ratio into a 0-100 signal.

        Values outside the valid range are safely clamped.
        """
        if ratio is None:
            return 0.0

        normalized = max(
            0.0,
            min(1.0, float(ratio)),
        )

        return normalized * 100.0

    @staticmethod
    def _observation_volume_signal(
        observation_count: Optional[int],
        expected_observation_count: Optional[int],
    ) -> float:
        """
        Convert observation volume into a 0-100 signal.

        The ratio is capped at 1.0, so collecting more observations
        than the expected count does not produce a score above 100.
        """
        if observation_count is None:
            return 0.0

        if expected_observation_count is None:
            return 0.0

        if observation_count < 0:
            return 0.0

        if expected_observation_count <= 0:
            return 0.0

        ratio = (
            float(observation_count)
            / float(expected_observation_count)
        )

        return ConfidenceSupportScorer._ratio_signal(
            ratio
        )

    def _freshness_signal(
        self,
        freshness_hours: Optional[float],
    ) -> float:
        """
        Convert freshness into a 0-100 signal.

        0 hours old = 100.
        maximum_freshness_hours or older = 0.

        The maximum freshness value is configurable and is an
        Intelligence-layer implementation choice.
        """
        if freshness_hours is None:
            return 0.0

        freshness = max(
            0.0,
            float(freshness_hours),
        )

        if freshness >= self.maximum_freshness_hours:
            return 0.0

        signal = (
            1.0
            - freshness
            / self.maximum_freshness_hours
        )

        return self._clamp(
            signal * 100.0
        )

    @staticmethod
    def _anomaly_signal(
        anomaly_available: bool,
    ) -> float:
        return 100.0 if anomaly_available else 0.0

    @staticmethod
    def _level(score: float) -> str:
        if score < 25:
            return "LOW"

        if score < 50:
            return "MODERATE"

        if score < 75:
            return "HIGH"

        return "VERY_HIGH"

    def calculate(
        self,
        route: str,
        booking_window: str,
        coverage_ratio: Optional[float],
        cross_source_agreement: Optional[float] = None,
        anomaly_available: bool = False,
        source_coverage: Optional[float] = None,
        observation_count: Optional[int] = None,
        expected_observation_count: Optional[int] = None,
        data_quality: Optional[float] = None,
        freshness_hours: Optional[float] = None,
    ) -> ConfidenceSupportResult:

        if coverage_ratio is None:
            return ConfidenceSupportResult(
                route=route,
                booking_window=booking_window,
                confidence_score=None,
                confidence_level="INSUFFICIENT_DATA",
                coverage_ratio=None,
                cross_source_agreement=(
                    cross_source_agreement
                ),
                anomaly_available=anomaly_available,
                source_coverage=source_coverage,
                observation_count=observation_count,
                expected_observation_count=(
                    expected_observation_count
                ),
                observation_volume_ratio=None,
                data_quality=data_quality,
                freshness_hours=freshness_hours,
                reason=(
                    "Insufficient coverage information."
                ),
            )

        # ---------------------------------------------------------
        # Build the signals that are actually available.
        #
        # Missing optional information is excluded from the
        # denominator so that unavailable data does not
        # artificially reduce confidence support.
        # ---------------------------------------------------------

        signals = {
            "coverage": self._ratio_signal(
                coverage_ratio
            )
        }

        weights = {
            "coverage": self.coverage_weight
        }

        observation_volume_ratio: Optional[float] = None

        if (
            observation_count is not None
            and expected_observation_count is not None
            and expected_observation_count > 0
            and observation_count >= 0
        ):
            observation_volume_ratio = min(
                1.0,
                float(observation_count)
                / float(expected_observation_count),
            )

            signals["observation_volume"] = (
                self._observation_volume_signal(
                    observation_count,
                    expected_observation_count,
                )
            )

            weights["observation_volume"] = (
                self.observation_volume_weight
            )

        if source_coverage is not None:
            signals["source_coverage"] = (
                self._ratio_signal(
                    source_coverage
                )
            )

            weights["source_coverage"] = (
                self.source_coverage_weight
            )

        if cross_source_agreement is not None:
            signals["agreement"] = (
                self._ratio_signal(
                    cross_source_agreement
                )
            )

            weights["agreement"] = (
                self.agreement_weight
            )

        if data_quality is not None:
            signals["data_quality"] = (
                self._ratio_signal(
                    data_quality
                )
            )

            weights["data_quality"] = (
                self.data_quality_weight
            )

        if freshness_hours is not None:
            signals["freshness"] = (
                self._freshness_signal(
                    freshness_hours
                )
            )

            weights["freshness"] = (
                self.freshness_weight
            )

        # Anomaly availability is always a known boolean.
        signals["anomaly"] = self._anomaly_signal(
            anomaly_available
        )

        weights["anomaly"] = self.anomaly_weight

        # ---------------------------------------------------------
        # Renormalize using only available signals.
        # ---------------------------------------------------------

        available_weight = sum(
            weights.values()
        )

        if available_weight <= 0:
            return ConfidenceSupportResult(
                route=route,
                booking_window=booking_window,
                confidence_score=None,
                confidence_level="INSUFFICIENT_DATA",
                coverage_ratio=coverage_ratio,
                cross_source_agreement=(
                    cross_source_agreement
                ),
                anomaly_available=anomaly_available,
                source_coverage=source_coverage,
                observation_count=observation_count,
                expected_observation_count=(
                    expected_observation_count
                ),
                observation_volume_ratio=(
                    observation_volume_ratio
                ),
                data_quality=data_quality,
                freshness_hours=freshness_hours,
                reason=(
                    "No valid confidence-support "
                    "signals are available."
                ),
            )

        score = sum(
            signals[name]
            * (
                weights[name]
                / available_weight
            )
            for name in signals
        )

        score = round(
            self._clamp(score),
            2,
        )

        level = self._level(score)

        reason_parts = [
            (
                f"Confidence support score is "
                f"{score}/100 based on available "
                f"coverage, source agreement, "
                f"observation quality, freshness, "
                f"and anomaly evidence."
            )
        ]

        reason_parts.append(
            f" Route coverage was "
            f"{self._ratio_signal(coverage_ratio):.1f}%."
        )

        if source_coverage is not None:
            reason_parts.append(
                f" Source coverage was "
                f"{self._ratio_signal(source_coverage):.1f}%."
            )

        if observation_volume_ratio is not None:
            reason_parts.append(
                f" Observation volume was "
                f"{observation_volume_ratio * 100:.1f}% "
                f"of expected."
            )

        if cross_source_agreement is not None:
            reason_parts.append(
                f" Cross-source agreement was "
                f"{self._ratio_signal(cross_source_agreement):.1f}%."
            )

        if data_quality is not None:
            reason_parts.append(
                f" Data quality signal was "
                f"{self._ratio_signal(data_quality):.1f}/100."
            )

        if freshness_hours is not None:
            reason_parts.append(
                f" Freshness was "
                f"{max(0.0, float(freshness_hours)):.2f} hours."
            )

        reason_parts.append(
            " Anomaly evidence was "
            + (
                "available."
                if anomaly_available
                else "not available."
            )
        )

        return ConfidenceSupportResult(
            route=route,
            booking_window=booking_window,
            confidence_score=score,
            confidence_level=level,
            coverage_ratio=coverage_ratio,
            cross_source_agreement=(
                cross_source_agreement
            ),
            anomaly_available=anomaly_available,
            source_coverage=source_coverage,
            observation_count=observation_count,
            expected_observation_count=(
                expected_observation_count
            ),
            observation_volume_ratio=(
                observation_volume_ratio
            ),
            data_quality=data_quality,
            freshness_hours=freshness_hours,
            reason="".join(reason_parts),
        )