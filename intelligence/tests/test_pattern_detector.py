import unittest

from intelligence.patterns.detector import (
    PatternDetector,
    PatternType,
)
from intelligence.models.result import IntelligenceStatus


class TestPatternDetector(unittest.TestCase):

    def setUp(self):
        self.detector = PatternDetector()

    def test_upward_pattern(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            index_values=[100.0, 102.0, 104.0, 107.0],
        )

        self.assertTrue(result["detected"])
        self.assertEqual(result["pattern"], PatternType.UPWARD)
        self.assertEqual(
            result["consecutive_movements"],
            3,
        )
        self.assertEqual(
            result["status"],
            IntelligenceStatus.SUCCESS.value,
        )

    def test_downward_pattern(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            index_values=[110.0, 108.0, 105.0, 102.0],
        )

        self.assertTrue(result["detected"])
        self.assertEqual(result["pattern"], PatternType.DOWNWARD)

    def test_stable_pattern(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            index_values=[100.0, 101.0, 100.5, 101.2],
        )

        self.assertFalse(result["detected"])
        self.assertEqual(result["pattern"], PatternType.STABLE)

    def test_insufficient_data(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            index_values=[100.0, 102.0],
        )

        self.assertFalse(result["detected"])
        self.assertEqual(
            result["pattern"],
            PatternType.INSUFFICIENT_DATA,
        )
        self.assertEqual(
            result["status"],
            IntelligenceStatus.INSUFFICIENT_DATA.value,
        )

    def test_average_change(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            index_values=[100.0, 102.0, 104.0, 107.0],
        )

        self.assertAlmostEqual(
            result["average_change"],
            7.0 / 3.0,
        )


if __name__ == "__main__":
    unittest.main()