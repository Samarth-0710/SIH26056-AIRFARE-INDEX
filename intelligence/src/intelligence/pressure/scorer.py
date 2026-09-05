from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AirfarePressureResult:
    """Supporting airfare pressure signal.

    This score does not modify or replace the official statistical index.
    """

    route: str
    booking_window: str
    pressure_score: Optional[float]
    pressure_level: str
    percentage_change: Optional[float]
    anomaly_score: Optional[float]
    cross_source_agreement: Optional[float]
    reason: str

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "booking_window": self.booking_window,
            "pressure_score": self.pressure_score,
            "pressure_level": self.pressure_level,
            "percentage_change": self.percentage_change,
            "anomaly_score": self.anomaly_score,
            "cross_source_agreement": self.cross_source_agreement,
            "reason": self.reason,
        }


class AirfarePressureScorer:
    """
    Calculates an interpretable 0-100 airfare pressure score.

    Components:
      - magnitude of recent airfare movement
      - anomaly signal
      - cross-source agreement

    This is an Intelligence-layer supporting indicator, not an
    official CPI/index calculation.
    """

    def __init__(
        self,
        movement_weight: float = 0.50,
        anomaly_weight: float = 0.25,
        agreement_weight: float = 0.25,
    ) -> None:
        total = movement_weight + anomaly_weight + agreement_weight

        if total <= 0:
            raise ValueError("At least one weight must be positive.")

        self.movement_weight = movement_weight / total
        self.anomaly_weight = anomaly_weight / total
        self.agreement_weight = agreement_weight / total

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _movement_signal(percentage_change: float) -> float:
        """
        Convert absolute percentage movement into a 0-100 signal.

        0% movement = 0 pressure.
        20% or greater movement = 100 pressure.
        """
        return AirfarePressureScorer._clamp(
            abs(percentage_change) / 20.0 * 100.0
        )

    @staticmethod
    def _anomaly_signal(anomaly_score: Optional[float]) -> float:
        if anomaly_score is None:
            return 0.0

        return AirfarePressureScorer._clamp(
            abs(float(anomaly_score))
        )

    @staticmethod
    def _agreement_signal(agreement_ratio: Optional[float]) -> float:
        if agreement_ratio is None:
            return 0.0

        return AirfarePressureScorer._clamp(
            float(agreement_ratio) * 100.0
        )

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
        percentage_change: Optional[float],
        anomaly_score: Optional[float] = None,
        cross_source_agreement: Optional[float] = None,
    ) -> AirfarePressureResult:
        if percentage_change is None:
            return AirfarePressureResult(
                route=route,
                booking_window=booking_window,
                pressure_score=None,
                pressure_level="INSUFFICIENT_DATA",
                percentage_change=None,
                anomaly_score=anomaly_score,
                cross_source_agreement=cross_source_agreement,
                reason="Insufficient fare movement data.",
            )

        movement_signal = self._movement_signal(percentage_change)
        anomaly_signal = self._anomaly_signal(anomaly_score)
        agreement_signal = self._agreement_signal(
            cross_source_agreement
        )

        score = (
            movement_signal * self.movement_weight
            + anomaly_signal * self.anomaly_weight
            + agreement_signal * self.agreement_weight
        )

        score = round(self._clamp(score), 2)
        level = self._level(score)

        direction = (
            "increased"
            if percentage_change > 0
            else "decreased"
            if percentage_change < 0
            else "remained stable"
        )

        reason = (
            f"Fare pressure score is {score}/100 because the fare "
            f"{direction} by {abs(percentage_change):.2f}%."
        )

        return AirfarePressureResult(
            route=route,
            booking_window=booking_window,
            pressure_score=score,
            pressure_level=level,
            percentage_change=percentage_change,
            anomaly_score=anomaly_score,
            cross_source_agreement=cross_source_agreement,
            reason=reason,
        )