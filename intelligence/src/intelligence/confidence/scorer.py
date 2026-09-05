from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ConfidenceSupportResult:
    """Supporting confidence signal for an intelligence result.

    This is NOT a statistical confidence interval and does not modify
    the official airfare index.
    """

    route: str
    booking_window: str
    confidence_score: Optional[float]
    confidence_level: str
    coverage_ratio: Optional[float]
    cross_source_agreement: Optional[float]
    anomaly_available: bool
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
            "reason": self.reason,
        }


class ConfidenceSupportScorer:
    """
    Produces an interpretable 0-100 supporting confidence score.

    Signals:
      - data coverage
      - cross-source agreement
      - availability of anomaly evidence

    This score is an Intelligence-layer diagnostic signal.
    It is not an official statistical confidence measure.
    """

    def __init__(
        self,
        coverage_weight: float = 0.50,
        agreement_weight: float = 0.30,
        anomaly_weight: float = 0.20,
    ) -> None:
        total = coverage_weight + agreement_weight + anomaly_weight

        if total <= 0:
            raise ValueError("At least one weight must be positive.")

        self.coverage_weight = coverage_weight / total
        self.agreement_weight = agreement_weight / total
        self.anomaly_weight = anomaly_weight / total

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(100.0, value))

    @staticmethod
    def _coverage_signal(
        coverage_ratio: Optional[float],
    ) -> float:
        if coverage_ratio is None:
            return 0.0

        return ConfidenceSupportScorer._clamp(
            float(coverage_ratio) * 100.0
        )

    @staticmethod
    def _agreement_signal(
        agreement_ratio: Optional[float],
    ) -> float:
        if agreement_ratio is None:
            return 0.0

        return ConfidenceSupportScorer._clamp(
            float(agreement_ratio) * 100.0
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
    ) -> ConfidenceSupportResult:

        if coverage_ratio is None:
            return ConfidenceSupportResult(
                route=route,
                booking_window=booking_window,
                confidence_score=None,
                confidence_level="INSUFFICIENT_DATA",
                coverage_ratio=None,
                cross_source_agreement=cross_source_agreement,
                anomaly_available=anomaly_available,
                reason="Insufficient coverage information.",
            )

        coverage_signal = self._coverage_signal(coverage_ratio)
        agreement_signal = self._agreement_signal(
            cross_source_agreement
        )
        anomaly_signal = self._anomaly_signal(
            anomaly_available
        )

        score = (
            coverage_signal * self.coverage_weight
            + agreement_signal * self.agreement_weight
            + anomaly_signal * self.anomaly_weight
        )

        score = round(self._clamp(score), 2)

        return ConfidenceSupportResult(
            route=route,
            booking_window=booking_window,
            confidence_score=score,
            confidence_level=self._level(score),
            coverage_ratio=coverage_ratio,
            cross_source_agreement=cross_source_agreement,
            anomaly_available=anomaly_available,
            reason=(
                f"Confidence support score is {score}/100 based on "
                "coverage, cross-source agreement, and available "
                "anomaly evidence."
            ),
        )