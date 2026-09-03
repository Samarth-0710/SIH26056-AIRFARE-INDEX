"""30-day back-test validation framework.

Evaluates calculated index series against externally supplied reference/historical data
across documented metrics.

IMPORTANT:
Does NOT fabricate official DGCA or government data.
Consumes external reference series provided by researchers or official benchmark tables.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from statistical_engine.models.observation import BookingWindow
from statistical_engine.models.validation_result import BacktestResult, ValidationMetrics
from statistical_engine.validation.metrics import compute_all_validation_metrics


class BacktestRunner:
    """Reusable back-test runner evaluating daily index series against reference benchmarks."""

    def __init__(
        self,
        reference_series_by_window: Dict[BookingWindow, Dict[date, float]],
        reference_source_name: str,
        is_official_reference: bool = False,
        expected_window_days: int = 30,
    ) -> None:
        """Initialize runner with external reference benchmark series.
        
        Args:
            reference_series_by_window: Mapping of booking window -> (date -> reference index)
            reference_source_name: Identifier of benchmark source (e.g. 'DGCA_MONTHLY_BULLETIN_2024')
            is_official_reference: Whether this reference dataset is officially published/sanctioned
            expected_window_days: Expected length of backtest window in days (default: 30)
        """
        self.reference_series = reference_series_by_window
        self.reference_source = reference_source_name
        self.is_official_reference = is_official_reference
        self.expected_days = expected_window_days

    def evaluate_window(
        self,
        calculated_series_by_window: Dict[BookingWindow, Dict[date, float]],
        start_date: date,
        end_date: date,
    ) -> BacktestResult:
        """Evaluate calculated daily index series against reference series between start_date and end_date.
        
        Aligns dates, detects missing entries, and computes metrics for each booking window.
        """
        warnings: List[str] = []
        total_calendar_days = (end_date - start_date).days + 1

        if total_calendar_days <= 0:
            raise ValueError(f"Invalid date range: start {start_date} is after end {end_date}")

        metrics_by_window: Dict[BookingWindow, ValidationMetrics] = {}
        all_matched_days_count = 0

        for bw in BookingWindow:
            calc_dict = calculated_series_by_window.get(bw, {})
            ref_dict = self.reference_series.get(bw, {})

            # Find matching dates within [start_date, end_date]
            aligned_calc: List[float] = []
            aligned_ref: List[float] = []

            curr_d = start_date
            missing_dates = []
            while curr_d <= end_date:
                val_c = calc_dict.get(curr_d)
                val_r = ref_dict.get(curr_d)
                if val_c is not None and val_r is not None:
                    aligned_calc.append(val_c)
                    aligned_ref.append(val_r)
                else:
                    missing_dates.append(curr_d)
                curr_d += timedelta(days=1)

            matched_count = len(aligned_calc)
            all_matched_days_count = max(all_matched_days_count, matched_count)

            if missing_dates:
                warnings.append(
                    f"[{bw.value}] Missing {len(missing_dates)} dates out of {total_calendar_days} expected days."
                )

            val_metrics = compute_all_validation_metrics(
                calculated_series=aligned_calc,
                reference_series=aligned_ref,
                expected_calendar_days=total_calendar_days,
            )
            metrics_by_window[bw] = val_metrics

        overall_status = "COMPLETED" if all_matched_days_count >= (total_calendar_days * 0.5) else "LOW_DATA"

        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            expected_days=total_calendar_days,
            matched_days=all_matched_days_count,
            booking_window_metrics=metrics_by_window,
            reference_source=self.reference_source,
            is_official_reference=self.is_official_reference,
            status=overall_status,
            warnings=warnings,
        )


def generate_demo_test_reference_series(
    start_date: date,
    days: int = 30,
    base_value: float = 100.0,
) -> Dict[BookingWindow, Dict[date, float]]:
    """Generates synthetic test benchmark series for testing only.
    
    CRITICAL: Marked as test fixture ONLY. Never to be presented as official DGCA data.
    """
    import math

    result: Dict[BookingWindow, Dict[date, float]] = {}
    for i, bw in enumerate(BookingWindow):
        series: Dict[date, float] = {}
        for d in range(days):
            cur_date = start_date + timedelta(days=d)
            # Gentle deterministic sinusoid for testing
            val = base_value + 5.0 * math.sin(d / 5.0 + i)
            series[cur_date] = round(val, 2)
        result[bw] = series

    return result
