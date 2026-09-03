"""Tests for price relative calculations."""

import unittest

from statistical_engine.core.price_relatives import calculate_price_relative
from statistical_engine.models.observation import BookingWindow


class TestPriceRelatives(unittest.TestCase):
    """Test price relative calculation and edge cases."""

    def test_normal_relative(self):
        rel = calculate_price_relative(
            current_fare=5500.0,
            previous_fare=5000.0,
            fingerprint="FP1",
            route="DEL-BOM",
            booking_window=BookingWindow.T_7,
        )
        self.assertIsNotNone(rel)
        self.assertAlmostEqual(rel.relative, 1.1)
        self.assertEqual(rel.route, "DEL-BOM")

    def test_zero_fare_handled(self):
        self.assertIsNone(calculate_price_relative(0.0, 5000.0))
        self.assertIsNone(calculate_price_relative(5000.0, 0.0))

    def test_negative_fare_handled(self):
        self.assertIsNone(calculate_price_relative(-500.0, 5000.0))
        self.assertIsNone(calculate_price_relative(5000.0, -500.0))

    def test_nan_inf_handled(self):
        self.assertIsNone(calculate_price_relative(float("nan"), 5000.0))
        self.assertIsNone(calculate_price_relative(5000.0, float("nan")))
        self.assertIsNone(calculate_price_relative(float("inf"), 5000.0))
        self.assertIsNone(calculate_price_relative(5000.0, float("inf")))


if __name__ == "__main__":
    unittest.main()
