from typing import List, Optional

from intelligence.models.result import IntelligenceStatus


class PatternType:
    """
    Supported deterministic airfare index patterns.
    """

    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"
    STABLE = "STABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class PatternDetector:
    """
    Detects persistent directional patterns in airfare index values.

    This component provides supporting intelligence only.
    It does not calculate or modify the official statistical index.
    """

    def __init__(
        self,
        minimum_change: float = 1.0,
        minimum_consecutive_movements: int = 3,
    ):
        self.minimum_change = minimum_change
        self.minimum_consecutive_movements = minimum_consecutive_movements

    def detect(
        self,
        route: str,
        booking_window: str,
        index_values: List[float],
    ) -> dict:
        """
        Detect a persistent upward or downward movement.

        index_values must be ordered from oldest to newest.
        """

        if len(index_values) < self.minimum_consecutive_movements + 1:
            return {
                "route": route,
                "booking_window": booking_window,
                "pattern": PatternType.INSUFFICIENT_DATA,
                "detected": False,
                "consecutive_movements": 0,
                "average_change": None,
                "status": IntelligenceStatus.INSUFFICIENT_DATA.value,
                "reason": (
                    "Insufficient historical index values "
                    "for pattern detection."
                ),
            }

        # Calculate movement between consecutive index observations.
        changes = [
            index_values[i] - index_values[i - 1]
            for i in range(1, len(index_values))
        ]

        # Only examine the most recent required movements.
        recent_changes = changes[
            -self.minimum_consecutive_movements:
        ]

        average_change = sum(recent_changes) / len(recent_changes)

        all_upward = all(
            change >= self.minimum_change
            for change in recent_changes
        )

        all_downward = all(
            change <= -self.minimum_change
            for change in recent_changes
        )

        if all_upward:
            pattern = PatternType.UPWARD
            detected = True
            reason = (
                f"Persistent upward pattern detected across "
                f"{self.minimum_consecutive_movements} consecutive "
                f"movements."
            )

        elif all_downward:
            pattern = PatternType.DOWNWARD
            detected = True
            reason = (
                f"Persistent downward pattern detected across "
                f"{self.minimum_consecutive_movements} consecutive "
                f"movements."
            )

        else:
            pattern = PatternType.STABLE
            detected = False
            reason = (
                "No persistent directional pattern detected "
                "in the recent movements."
            )

        return {
            "route": route,
            "booking_window": booking_window,
            "pattern": pattern,
            "detected": detected,
            "consecutive_movements": len(recent_changes),
            "average_change": average_change,
            "status": IntelligenceStatus.SUCCESS.value,
            "reason": reason,
        }