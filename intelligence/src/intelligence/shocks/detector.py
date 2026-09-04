from typing import Dict, List, Optional


class ShockSeverity:
    """
    Severity levels for detected airfare shocks.
    """

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ShockDetector:
    """
    Detects unusually large movements in airfare index values.

    This is a supporting intelligence component.
    It does not calculate, replace, or modify the statistical index.

    Thresholds used here are implementation parameters and are not
    official MoSPI/CPI thresholds.
    """

    def __init__(
        self,
        low_threshold: float = 5.0,
        medium_threshold: float = 10.0,
        high_threshold: float = 20.0,
    ):
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold

    def detect(
        self,
        route_indices: Dict[str, Optional[float]],
        previous_route_indices: Dict[str, Optional[float]],
    ) -> Dict:
        """
        Detect a potential shock from route-level index movements.

        route_indices:
            Current route index values.

        previous_route_indices:
            Previous observation's route index values.

        Only routes available in both dictionaries and having valid
        numeric values are considered.
        """

        movements: List[Dict] = []

        for route, current_index in route_indices.items():
            previous_index = previous_route_indices.get(route)

            if current_index is None or previous_index is None:
                continue

            if previous_index == 0:
                continue

            percentage_change = (
                (current_index - previous_index)
                / previous_index
            ) * 100.0

            movements.append(
                {
                    "route": route,
                    "current_index": current_index,
                    "previous_index": previous_index,
                    "percentage_change": percentage_change,
                    "absolute_change": abs(percentage_change),
                }
            )

        if not movements:
            return {
                "detected": False,
                "severity": ShockSeverity.NONE,
                "average_movement": None,
                "maximum_movement": None,
                "affected_routes": [],
                "movements": [],
                "reason": (
                    "Insufficient comparable route-level data "
                    "for shock detection."
                ),
            }

        average_movement = sum(
            movement["percentage_change"]
            for movement in movements
        ) / len(movements)

        maximum_movement = max(
            movements,
            key=lambda movement: movement["absolute_change"],
        )

        maximum_absolute_movement = (
            maximum_movement["absolute_change"]
        )

        severity = self._classify_severity(
            maximum_absolute_movement
        )

        detected = severity != ShockSeverity.NONE

        affected_routes = [
            movement["route"]
            for movement in movements
            if movement["absolute_change"]
            >= self.low_threshold
        ]

        if detected:
            direction = (
                "upward"
                if average_movement > 0
                else "downward"
            )

            reason = (
                f"Potential {direction} airfare shock detected. "
                f"Maximum route movement was "
                f"{maximum_absolute_movement:.2f}%."
            )
        else:
            reason = (
                "No significant broad route-level shock detected."
            )

        return {
            "detected": detected,
            "severity": severity,
            "average_movement": average_movement,
            "maximum_movement": maximum_absolute_movement,
            "affected_routes": affected_routes,
            "movements": movements,
            "reason": reason,
        }

    def _classify_severity(
        self,
        movement: float,
    ) -> str:

        if movement >= self.high_threshold:
            return ShockSeverity.HIGH

        if movement >= self.medium_threshold:
            return ShockSeverity.MEDIUM

        if movement >= self.low_threshold:
            return ShockSeverity.LOW

        return ShockSeverity.NONE