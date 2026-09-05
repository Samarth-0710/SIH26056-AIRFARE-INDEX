from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Optional


@dataclass(frozen=True)
class MissingDataSupportResult:
    """Supporting result for a missing fare observation.

    This result represents an estimate only. It does not
    automatically replace a missing value in the official
    Statistical Engine.
    """

    route: str
    booking_window: str
    estimated_fare: Optional[float]
    comparable_observations: int
    confidence: str
    used: bool

    # Explicit estimation/provenance information.
    original_value_missing: bool
    estimated: bool
    estimation_method: Optional[str]

    reason: str

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "booking_window": self.booking_window,
            "estimated_fare": self.estimated_fare,
            "comparable_observations": (
                self.comparable_observations
            ),
            "confidence": self.confidence,
            "used": self.used,
            "original_value_missing": (
                self.original_value_missing
            ),
            "estimated": self.estimated,
            "estimation_method": (
                self.estimation_method
            ),
            "reason": self.reason,
        }


class MissingDataSupporter:
    """
    Provides a conservative supporting estimate for a missing fare.

    The estimate uses the median of comparable observed fares.

    This component is Intelligence-layer support only.

    It does NOT:
      - replace missing values automatically
      - modify the official Statistical Engine
      - classify an estimate as an actual observation
      - decide whether imputation is permitted for the official index
    """

    def __init__(
        self,
        minimum_observations: int = 3,
    ) -> None:
        if minimum_observations < 1:
            raise ValueError(
                "minimum_observations must be at least 1"
            )

        self.minimum_observations = (
            minimum_observations
        )

    @staticmethod
    def _valid_fares(
        fares: Iterable[float],
    ) -> list[float]:
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
        valid_fares = self._valid_fares(
            comparable_fares
        )

        count = len(valid_fares)

        # ---------------------------------------------------------
        # Insufficient comparable observations.
        #
        # No estimate is produced and nothing is marked as used.
        # ---------------------------------------------------------

        if count < self.minimum_observations:
            return MissingDataSupportResult(
                route=route,
                booking_window=booking_window,
                estimated_fare=None,
                comparable_observations=count,
                confidence="INSUFFICIENT_DATA",
                used=False,
                original_value_missing=True,
                estimated=False,
                estimation_method=None,
                reason=(
                    "Insufficient comparable observations "
                    "for a supporting missing-data estimate. "
                    "No replacement value was produced."
                ),
            )

        # ---------------------------------------------------------
        # Conservative estimate.
        #
        # Median is used because it is less sensitive to extreme
        # observations than the arithmetic mean.
        # ---------------------------------------------------------

        estimated_fare = round(
            median(valid_fares),
            2,
        )

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
            original_value_missing=True,
            estimated=True,
            estimation_method="MEDIAN",
            reason=(
                f"Supporting estimate based on the median "
                f"of {count} comparable observations. "
                "The estimated value must remain explicitly "
                "identified as estimated and must not be "
                "silently treated as an actual fare."
            ),
        )