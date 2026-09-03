"""Tests for Jevons geometric mean index calculations."""

import math
import unittest

from statistical_engine.core.jevons import calculate_jevons_index
from statistical_engine.models.index_result import CalculationStatus


class TestJevonsIndex(unittest.TestCase):
    """Test Jevons elementary formula and mathematical correctness."""

    def test_single_pair(self):
        relatives = [1.25]
        res = calculate_jevons_index(relatives)
        self.assertEqual(res.status, CalculationStatus.SUCCESS)
        self.assertEqual(res.valid_pairs_count, 1)
        self.assertAlmostEqual(res.index_value, 125.0)
        self.assertAlmostEqual(res.geometric_mean, 1.25)

    def test_multiple_pairs_hand_calculated(self):
        # 3 relatives: 1.25, 1.0, 1.25
        # product = 1.5625
        # GM = (1.5625)^(1/3) = 1.16039788862...
        # Index = 116.039788862...
        relatives = [1.25, 1.0, 1.25]
        expected_gm = (1.25 * 1.0 * 1.25) ** (1.0 / 3.0)
        expected_index = expected_gm * 100.0

        res = calculate_jevons_index(relatives)
        self.assertEqual(res.status, CalculationStatus.SUCCESS)
        self.assertEqual(res.valid_pairs_count, 3)
        self.assertAlmostEqual(res.geometric_mean, expected_gm, places=7)
        self.assertAlmostEqual(res.index_value, expected_index, places=7)

    def test_two_pairs_inverse_movements(self):
        # 1.20 and 0.80 -> GM = sqrt(0.96) = 0.97979589711
        relatives = [1.20, 0.80]
        expected_gm = math.sqrt(1.20 * 0.80)
        expected_index = expected_gm * 100.0

        res = calculate_jevons_index(relatives)
        self.assertEqual(res.status, CalculationStatus.SUCCESS)
        self.assertAlmostEqual(res.geometric_mean, expected_gm, places=7)
        self.assertAlmostEqual(res.index_value, expected_index, places=7)

    def test_empty_pairs(self):
        res = calculate_jevons_index([])
        self.assertEqual(res.status, CalculationStatus.INSUFFICIENT_DATA)
        self.assertIsNone(res.index_value)
        self.assertEqual(res.valid_pairs_count, 0)

    def test_invalid_pairs_filtered(self):
        # Contains 0, negative, nan, and one valid 1.2
        relatives = [0.0, -1.5, float("nan"), 1.2]
        res = calculate_jevons_index(relatives)
        self.assertEqual(res.status, CalculationStatus.SUCCESS)
        self.assertEqual(res.valid_pairs_count, 1)
        self.assertAlmostEqual(res.index_value, 120.0)

    def test_all_invalid_pairs(self):
        relatives = [0.0, -2.0, float("nan")]
        res = calculate_jevons_index(relatives)
        self.assertEqual(res.status, CalculationStatus.INSUFFICIENT_DATA)
        self.assertIsNone(res.index_value)


if __name__ == "__main__":
    unittest.main()
