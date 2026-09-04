from typing import Optional

from intelligence.models.result import AnomalyResult


class AnomalyExplainer:
    """
    Converts an anomaly result into a human-readable explanation.

    This component does not calculate or modify the statistical index.
    """

    def explain(self, result: AnomalyResult) -> str:
        if not result.detected:
            return (
                f"No significant anomaly detected for "
                f"{result.route} ({result.booking_window})."
            )

        if result.percentage_change is None:
            return (
                f"Anomaly detected for {result.route} "
                f"({result.booking_window}), but the percentage "
                f"movement could not be determined."
            )

        direction = (
            "increased"
            if result.percentage_change > 0
            else "decreased"
        )

        return (
            f"{result.route} ({result.booking_window}) "
            f"airfare index {direction} by "
            f"{abs(result.percentage_change):.2f}% "
            f"from {result.previous_index:.2f} "
            f"to {result.current_index:.2f}. "
            f"Severity: {result.severity.value}."
        )