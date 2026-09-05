from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AirfarePressureResult:
    """Supporting airfare pressure signal.

    This score is an Intelligence-layer analytical indicator.
    It does not modify or replace the official statistical index.
    """

    route: str
    booking_window: str
    pressure_score: Optional[float]
    pressure_level: str

    percentage_change: Optional[float]
    anomaly_score: Optional[float]
    cross_source_agreement: Optional[float]

    acceleration: Optional[float]
    route_coverage: Optional[float]
    source_coverage: Optional[float]
    lead_time_pressure: Optional[float]
    demand_availability_signal: Optional[float]

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
            "acceleration": self.acceleration,
            "route_coverage": self.route_coverage,
            "source_coverage": self.source_coverage,
            "lead_time_pressure": self.lead_time_pressure,
            "demand_availability_signal": self.demand_availability_signal,
            "reason": self.reason,
        }


class AirfarePressureScorer:
    """
    Calculates an interpretable 0-100 airfare pressure score.

    Supporting components:
      - recent fare movement
      - acceleration of fare movement
      - anomaly signal
      - cross-source agreement
      - route coverage
      - source coverage
      - lead-time pressure
      - optional demand/availability signal

    This is an Intelligence-layer supporting indicator.
    It is NOT an official CPI/index calculation.

    Default weights are analytical implementation choices and
    must not be interpreted as official statistical weights.

    When optional signals are unavailable, their weights are
    excluded from the calculation and the remaining available
    weights are renormalized. This prevents missing optional
    data from artificially lowering the score.
    """

    def __init__(
        self,
        movement_weight: float = 0.35,
        acceleration_weight: float = 0.15,
        anomaly_weight: float = 0.15,
        agreement_weight: float = 0.15,
        route_coverage_weight: float = 0.10,
        source_coverage_weight: float = 0.05,
        lead_time_weight: float = 0.05,
        demand_availability_weight: float = 0.00,
    ) -> None:

        weights = {
            "movement": movement_weight,
            "acceleration": acceleration_weight,
            "anomaly": anomaly_weight,
            "agreement": agreement_weight,
            "route_coverage": route_coverage_weight,
            "source_coverage": source_coverage_weight,
            "lead_time": lead_time_weight,
            "demand_availability": demand_availability_weight,
        }

        if any(weight < 0 for weight in weights.values()):
            raise ValueError("Weights cannot be negative.")

        total = sum(weights.values())

        if total <= 0:
            raise ValueError(
                "At least one weight must be positive."
            )

        self.movement_weight = movement_weight / total
        self.acceleration_weight = acceleration_weight / total
        self.anomaly_weight = anomaly_weight / total
        self.agreement_weight = agreement_weight / total
        self.route_coverage_weight = (
            route_coverage_weight / total
        )
        self.source_coverage_weight = (
            source_coverage_weight / total
        )
        self.lead_time_weight = lead_time_weight / total
        self.demand_availability_weight = (
            demand_availability_weight / total
        )

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 100.0,
    ) -> float:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _movement_signal(
        percentage_change: float,
    ) -> float:
        """
        Convert absolute fare movement into a 0-100 signal.

        0% movement = 0.
        20% or greater movement = 100.

        This threshold is an Intelligence-layer implementation
        choice, not an official CPI threshold.
        """
        return AirfarePressureScorer._clamp(
            abs(float(percentage_change)) / 20.0 * 100.0
        )

    @staticmethod
    def _acceleration_signal(
        acceleration: Optional[float],
    ) -> float:
        """
        Convert acceleration into a 0-100 signal.

        0 percentage points = 0.
        10 percentage points or greater = 100.

        This threshold is an Intelligence-layer implementation
        choice, not an official statistical threshold.
        """
        if acceleration is None:
            return 0.0

        return AirfarePressureScorer._clamp(
            abs(float(acceleration)) / 10.0 * 100.0
        )

    @staticmethod
    def _anomaly_signal(
        anomaly_score: Optional[float],
    ) -> float:
        if anomaly_score is None:
            return 0.0

        return AirfarePressureScorer._clamp(
            abs(float(anomaly_score))
        )

    @staticmethod
    def _ratio_signal(
        ratio: Optional[float],
    ) -> float:
        """
        Convert a normalized ratio in [0, 1] into a 0-100 signal.

        Values outside [0, 1] are safely clamped.
        """
        if ratio is None:
            return 0.0

        normalized_ratio = max(
            0.0,
            min(1.0, float(ratio)),
        )

        return normalized_ratio * 100.0

    @staticmethod
    def _lead_time_signal(
        lead_time_pressure: Optional[float],
    ) -> float:
        """
        Convert a normalized lead-time pressure signal into 0-100.

        Expected input range: 0-1.
        """
        if lead_time_pressure is None:
            return 0.0

        normalized_value = max(
            0.0,
            min(1.0, float(lead_time_pressure)),
        )

        return normalized_value * 100.0

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
        acceleration: Optional[float] = None,
        route_coverage: Optional[float] = None,
        source_coverage: Optional[float] = None,
        lead_time_pressure: Optional[float] = None,
        demand_availability_signal: Optional[float] = None,
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
                acceleration=acceleration,
                route_coverage=route_coverage,
                source_coverage=source_coverage,
                lead_time_pressure=lead_time_pressure,
                demand_availability_signal=(
                    demand_availability_signal
                ),
                reason="Insufficient fare movement data.",
            )

        # ---------------------------------------------------------
        # Build only the signals that are actually available.
        # Missing optional signals must not artificially reduce
        # the final score.
        # ---------------------------------------------------------

        signals = {
            "movement": self._movement_signal(
                percentage_change
            )
        }

        weights = {
            "movement": self.movement_weight
        }

        if acceleration is not None:
            signals["acceleration"] = (
                self._acceleration_signal(acceleration)
            )
            weights["acceleration"] = (
                self.acceleration_weight
            )

        if anomaly_score is not None:
            signals["anomaly"] = (
                self._anomaly_signal(anomaly_score)
            )
            weights["anomaly"] = self.anomaly_weight

        if cross_source_agreement is not None:
            signals["agreement"] = (
                self._ratio_signal(
                    cross_source_agreement
                )
            )
            weights["agreement"] = self.agreement_weight

        if route_coverage is not None:
            signals["route_coverage"] = (
                self._ratio_signal(route_coverage)
            )
            weights["route_coverage"] = (
                self.route_coverage_weight
            )

        if source_coverage is not None:
            signals["source_coverage"] = (
                self._ratio_signal(source_coverage)
            )
            weights["source_coverage"] = (
                self.source_coverage_weight
            )

        if lead_time_pressure is not None:
            signals["lead_time"] = (
                self._lead_time_signal(
                    lead_time_pressure
                )
            )
            weights["lead_time"] = self.lead_time_weight

        if demand_availability_signal is not None:
            signals["demand_availability"] = (
                self._lead_time_signal(
                    demand_availability_signal
                )
            )
            weights["demand_availability"] = (
                self.demand_availability_weight
            )

        # ---------------------------------------------------------
        # Renormalize weights using only available signals.
        # ---------------------------------------------------------

        available_weight = sum(weights.values())

        if available_weight <= 0:
            return AirfarePressureResult(
                route=route,
                booking_window=booking_window,
                pressure_score=None,
                pressure_level="INSUFFICIENT_DATA",
                percentage_change=percentage_change,
                anomaly_score=anomaly_score,
                cross_source_agreement=cross_source_agreement,
                acceleration=acceleration,
                route_coverage=route_coverage,
                source_coverage=source_coverage,
                lead_time_pressure=lead_time_pressure,
                demand_availability_signal=(
                    demand_availability_signal
                ),
                reason="No valid pressure signals are available.",
            )

        score = sum(
            signals[name]
            * (weights[name] / available_weight)
            for name in signals
        )

        score = round(
            self._clamp(score),
            2,
        )

        level = self._level(score)

        direction = (
            "increased"
            if percentage_change > 0
            else "decreased"
            if percentage_change < 0
            else "remained stable"
        )

        reason_parts = [
            (
                f"Fare pressure score is {score}/100 because "
                f"the fare {direction} by "
                f"{abs(percentage_change):.2f}%."
            )
        ]

        if acceleration is not None:
            acceleration_direction = (
                "accelerated upward"
                if acceleration > 0
                else "accelerated downward"
                if acceleration < 0
                else "showed no acceleration"
            )

            reason_parts.append(
                f" Movement {acceleration_direction} by "
                f"{abs(acceleration):.2f} percentage points."
            )

        if anomaly_score is not None:
            reason_parts.append(
                f" Anomaly signal was "
                f"{self._anomaly_signal(anomaly_score):.1f}/100."
            )

        if cross_source_agreement is not None:
            agreement_display = (
                self._ratio_signal(
                    cross_source_agreement
                )
            )

            reason_parts.append(
                f" Cross-source agreement was "
                f"{agreement_display:.1f}%."
            )

        if route_coverage is not None:
            coverage_display = (
                self._ratio_signal(route_coverage)
            )

            reason_parts.append(
                f" Route coverage was "
                f"{coverage_display:.1f}%."
            )

        if source_coverage is not None:
            coverage_display = (
                self._ratio_signal(source_coverage)
            )

            reason_parts.append(
                f" Source coverage was "
                f"{coverage_display:.1f}%."
            )

        if lead_time_pressure is not None:
            lead_time_display = (
                self._lead_time_signal(
                    lead_time_pressure
                )
            )

            reason_parts.append(
                f" Lead-time pressure signal was "
                f"{lead_time_display:.1f}/100."
            )

        if demand_availability_signal is not None:
            demand_display = (
                self._lead_time_signal(
                    demand_availability_signal
                )
            )

            reason_parts.append(
                f" Demand/availability signal was "
                f"{demand_display:.1f}/100."
            )

        reason = "".join(reason_parts)

        return AirfarePressureResult(
            route=route,
            booking_window=booking_window,
            pressure_score=score,
            pressure_level=level,
            percentage_change=percentage_change,
            anomaly_score=anomaly_score,
            cross_source_agreement=cross_source_agreement,
            acceleration=acceleration,
            route_coverage=route_coverage,
            source_coverage=source_coverage,
            lead_time_pressure=lead_time_pressure,
            demand_availability_signal=(
                demand_availability_signal
            ),
            reason=reason,
        )