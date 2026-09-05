from typing import Optional

from intelligence.models.result import (
    AnomalyResult,
    AnomalySeverity,
)


class AnomalyDetector:
    """
    Deterministic anomaly detector for Airfare Price Index movements.

    This is a supporting intelligence component.
    It does NOT calculate or modify the statistical index.
    """

    def __init__(
        self,
        low_threshold: float = 2.0,
        medium_threshold: float = 5.0,
        high_threshold: float = 10.0,
    ):
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold

    def detect(
        self,
        route: str,
        booking_window: str,
        current_index: Optional[float],
        previous_index: Optional[float],
    ) -> AnomalyResult:

        # Cannot calculate movement without both observations.
        if current_index is None or previous_index is None:
            return AnomalyResult(
                route=route,
                booking_window=booking_window,
                current_index=current_index,
                previous_index=previous_index,
                point_change=None,
                percentage_change=None,
                anomaly_score=None,
                severity=AnomalySeverity.NORMAL,
                detected=False,
                reason="Insufficient data for anomaly detection.",
            )

        if previous_index == 0:
            return AnomalyResult(
                route=route,
                booking_window=booking_window,
                current_index=current_index,
                previous_index=previous_index,
                point_change=None,
                percentage_change=None,
                anomaly_score=None,
                severity=AnomalySeverity.NORMAL,
                detected=False,
                reason="Previous index is zero; percentage change cannot be calculated.",
            )

        point_change = current_index - previous_index

        percentage_change = (
            point_change / previous_index
        ) * 100.0

        # Use absolute movement to detect both sharp increases
        # and sharp decreases.
        anomaly_score = abs(percentage_change)

        severity = self._classify_severity(anomaly_score)

        detected = severity != AnomalySeverity.NORMAL

        reason = None

        if detected:
            direction = (
                "increase"
                if percentage_change > 0
                else "decrease"
            )

            reason = (
                f"Unusual {direction} of "
                f"{abs(percentage_change):.2f}% "
                f"in the airfare index."
            )

        return AnomalyResult(
            route=route,
            booking_window=booking_window,
            current_index=current_index,
            previous_index=previous_index,
            point_change=point_change,
            percentage_change=percentage_change,
            anomaly_score=anomaly_score,
            severity=severity,
            detected=detected,
            reason=reason,
        )

    def _classify_severity(
        self,
        score: float,
    ) -> AnomalySeverity:

        if score >= self.high_threshold:
            return AnomalySeverity.HIGH

        if score >= self.medium_threshold:
            return AnomalySeverity.MEDIUM

        if score >= self.low_threshold:
            return AnomalySeverity.LOW

        return AnomalySeverity.NORMAL