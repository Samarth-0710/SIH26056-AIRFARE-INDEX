"""Tests for the 30-day back-test validation framework."""

from datetime import date, timedelta
import unittest

from statistical_engine.models.observation import BookingWindow
from statistical_engine.models.validation_result import MetricStatus
from statistical_engine.validation.backtest import (
    BacktestRunner,
    generate_demo_test_reference_series,
)


class TestBacktestFramework(unittest.TestCase):
    """Test 30-day backtest evaluation framework."""

    def test_backtest_evaluation_30_days(self):
        start_d = date(2024, 4, 1)
        end_d = date(2024, 4, 30)

        # Generate test reference series
        ref_series = generate_demo_test_reference_series(start_date=start_d, days=30)
        runner = BacktestRunner(
            reference_series_by_window=ref_series,
            reference_source_name="TEST_SYNTHETIC_BENCHMARK",
            is_official_reference=False,
            expected_window_days=30,
        )

        # Simulate calculated series with small noise around reference
        calc_series = {}
        for bw in BookingWindow:
            calc_series[bw] = {
                d: val + 0.5 for d, val in ref_series[bw].items()
            }

        result = runner.evaluate_window(calc_series, start_d, end_d)
        self.assertEqual(result.expected_days, 30)
        self.assertEqual(result.matched_days, 30)
        self.assertEqual(result.status, "COMPLETED")
        self.assertFalse(result.is_official_reference)

        # Check metrics for T+7
        t7_metrics = result.booking_window_metrics[BookingWindow.T_7]
        self.assertEqual(t7_metrics.mae.status, MetricStatus.VALID)
        self.assertAlmostEqual(t7_metrics.mae.value, 0.5)
        self.assertAlmostEqual(t7_metrics.coverage.value, 1.0)
        self.assertAlmostEqual(t7_metrics.pearson_correlation.value, 1.0)

    def test_backtest_with_missing_dates(self):
        start_d = date(2024, 4, 1)
        end_d = date(2024, 4, 30)

        ref_series = generate_demo_test_reference_series(start_date=start_d, days=30)
        runner = BacktestRunner(
            reference_series_by_window=ref_series,
            reference_source_name="TEST_BENCHMARK",
        )

        # Calculated series only has 20 of the 30 days
        calc_series = {}
        for bw in BookingWindow:
            calc_series[bw] = {
                start_d + timedelta(days=i): 100.0 + i for i in range(20)
            }

        result = runner.evaluate_window(calc_series, start_d, end_d)
        self.assertEqual(result.expected_days, 30)
        self.assertEqual(result.matched_days, 20)
        t7_metrics = result.booking_window_metrics[BookingWindow.T_7]
        self.assertAlmostEqual(t7_metrics.coverage.value, 20.0 / 30.0)
        self.assertTrue(len(result.warnings) > 0)


if __name__ == "__main__":
    unittest.main()
