"""Tests for statistical validation metrics."""

import math
import unittest

from statistical_engine.models.validation_result import MetricStatus
from statistical_engine.validation.metrics import (
    calculate_coverage,
    calculate_directional_accuracy,
    calculate_mae,
    calculate_pearson_correlation,
    calculate_rmse,
    calculate_spearman_correlation,
    calculate_stability,
    compute_all_validation_metrics,
)


class TestValidationMetrics(unittest.TestCase):
    """Test individual validation metrics and edge case handling."""

    def test_perfect_positive_correlation(self):
        a = [100.0, 102.0, 104.0, 106.0, 108.0]
        b = [200.0, 204.0, 208.0, 212.0, 216.0]
        res = calculate_pearson_correlation(a, b)
        self.assertEqual(res.status, MetricStatus.VALID)
        self.assertAlmostEqual(res.value, 1.0)

    def test_perfect_negative_correlation(self):
        a = [10.0, 20.0, 30.0, 40.0]
        b = [40.0, 30.0, 20.0, 10.0]
        res = calculate_pearson_correlation(a, b)
        self.assertEqual(res.status, MetricStatus.VALID)
        self.assertAlmostEqual(res.value, -1.0)

    def test_constant_series_undefined_variance(self):
        # Series b is constant (variance = 0)
        a = [100.0, 102.0, 104.0]
        b = [100.0, 100.0, 100.0]
        res = calculate_pearson_correlation(a, b)
        self.assertEqual(res.status, MetricStatus.UNDEFINED_VARIANCE)
        self.assertIsNone(res.value)

    def test_spearman_rank_correlation(self):
        # Monotonic non-linear relationship: x vs x^3
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.0, 8.0, 27.0, 64.0, 125.0]
        res = calculate_spearman_correlation(a, b)
        self.assertEqual(res.status, MetricStatus.VALID)
        self.assertAlmostEqual(res.value, 1.0)

    def test_mae_and_rmse_hand_calculated(self):
        # errors: |102 - 100| = 2, |97 - 100| = 3, |105 - 101| = 4
        # MAE = (2 + 3 + 4) / 3 = 9 / 3 = 3.0
        # RMSE = sqrt((4 + 9 + 16) / 3) = sqrt(29 / 3) = sqrt(9.6666667) = 3.109100...
        pred = [102.0, 97.0, 105.0]
        ref = [100.0, 100.0, 101.0]

        mae_res = calculate_mae(pred, ref)
        self.assertEqual(mae_res.status, MetricStatus.VALID)
        self.assertAlmostEqual(mae_res.value, 3.0)

        rmse_res = calculate_rmse(pred, ref)
        self.assertEqual(rmse_res.status, MetricStatus.VALID)
        self.assertAlmostEqual(rmse_res.value, math.sqrt(29.0 / 3.0))

    def test_directional_accuracy(self):
        # day 0 -> 1: pred +2, ref +5 (agree)
        # day 1 -> 2: pred -1, ref -3 (agree)
        # day 2 -> 3: pred +4, ref -2 (disagree)
        # 2 out of 3 changes match -> 2/3 = 0.666667
        pred = [100.0, 102.0, 101.0, 105.0]
        ref = [100.0, 105.0, 102.0, 100.0]

        res = calculate_directional_accuracy(pred, ref)
        self.assertEqual(res.status, MetricStatus.VALID)
        self.assertAlmostEqual(res.value, 2.0 / 3.0)

    def test_coverage(self):
        res = calculate_coverage(valid_observed_days=27, expected_calendar_days=30)
        self.assertEqual(res.status, MetricStatus.VALID)
        self.assertAlmostEqual(res.value, 0.9)

    def test_stability_hand_calculated(self):
        # series: [100, 102, 105, 103]
        # diffs: [2, 3, -2]
        # mean diff = (2 + 3 - 2) / 3 = 3 / 3 = 1.0
        # sum of sq diffs: (2 - 1)^2 + (3 - 1)^2 + (-2 - 1)^2 = 1 + 4 + 9 = 14
        # sample variance: 14 / (3 - 1) = 7.0
        # sample std: sqrt(7.0) = 2.64575...
        series = [100.0, 102.0, 105.0, 103.0]
        res = calculate_stability(series)
        self.assertEqual(res.status, MetricStatus.VALID)
        self.assertAlmostEqual(res.value, math.sqrt(7.0))

    def test_mismatched_series_lengths(self):
        a = [100.0, 101.0]
        b = [100.0, 101.0, 102.0]
        self.assertEqual(calculate_pearson_correlation(a, b).status, MetricStatus.MISMATCHED_LENGTH)
        self.assertEqual(calculate_mae(a, b).status, MetricStatus.MISMATCHED_LENGTH)
        self.assertEqual(calculate_rmse(a, b).status, MetricStatus.MISMATCHED_LENGTH)


if __name__ == "__main__":
    unittest.main()
