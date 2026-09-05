from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Optional


@dataclass(frozen=True)
class MissingDataSupportResult:
    """Supporting result for a missing fare observation.

    This does not automatically replace missing values in the
    official Statistical Engine.
    """

    route: str
    booking_window: str
    estimated_fare: Optional[float]
    comparable_observations: int
    confidence: str
    used: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "booking_window": self.booking_window,
            "estimated_fare": self.estimated_fare,
            "comparable_observations": self.comparable_observations,
            "confidence": self.confidence,
            "used": self.used,
            "reason": self.reason,
        }


class MissingDataSupporter:
    """
    Provides a conservative supporting estimate for a missing fare.

    The estimate uses the median of comparable observed fares.

    It is intended as supporting intelligence only. The official
    Statistical Engine must decide whether such an estimate is
    methodologically permitted for index calculation.
    """

    def __init__(self, minimum_observations: int = 3) -> None:
        if minimum_observations < 1:
            raise ValueError(
                "minimum_observations must be at least 1"
            )

        self.minimum_observations = minimum_observations

    @staticmethod
    def _valid_fares(fares: Iterable[float]) -> list[float]:
        valid = []

        for fare in fares:
            try:
                value = float(fare)
            except (TypeError, ValueError):
                continue

            if value > 0:
                valid.append(value)

        return valid

    def estimate(
        self,
        route: str,
        booking_window: str,
        comparable_fares: Iterable[float],
    ) -> MissingDataSupportResult:
        valid_fares = self._valid_fares(comparable_fares)

        count = len(valid_fares)

        if count < self.minimum_observations:
            return MissingDataSupportResult(
                route=route,
                booking_window=booking_window,
                estimated_fare=None,
                comparable_observations=count,
                confidence="INSUFFICIENT_DATA",
                used=False,
                reason=(
                    "Insufficient comparable observations for "
                    "a supporting missing-data estimate."
                ),
            )

        estimated_fare = round(median(valid_fares), 2)

        if count >= 5:
            confidence = "HIGH"
        else:
            confidence = "MODERATE"

        return MissingDataSupportResult(
            route=route,
            booking_window=booking_window,
            estimated_fare=estimated_fare,
            comparable_observations=count,
            confidence=confidence,
            used=True,
            reason=(
                f"Supporting estimate based on the median of "
                f"{count} comparable observations."
            ),
        )