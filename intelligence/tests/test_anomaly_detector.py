import unittest

from intelligence.anomaly.detector import AnomalyDetector
from intelligence.models.result import AnomalySeverity


class TestAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.detector = AnomalyDetector()

    def test_normal_movement(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=101.0,
            previous_index=100.0,
        )

        self.assertFalse(result.detected)
        self.assertEqual(result.severity, AnomalySeverity.NORMAL)
        self.assertAlmostEqual(result.point_change, 1.0)
        self.assertAlmostEqual(result.percentage_change, 1.0)

    def test_low_anomaly(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=103.0,
            previous_index=100.0,
        )

        self.assertTrue(result.detected)
        self.assertEqual(result.severity, AnomalySeverity.LOW)

    def test_medium_anomaly(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=106.0,
            previous_index=100.0,
        )

        self.assertTrue(result.detected)
        self.assertEqual(result.severity, AnomalySeverity.MEDIUM)

    def test_high_anomaly(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=115.0,
            previous_index=100.0,
        )

        self.assertTrue(result.detected)
        self.assertEqual(result.severity, AnomalySeverity.HIGH)

    def test_negative_anomaly(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=88.0,
            previous_index=100.0,
        )

        self.assertTrue(result.detected)
        self.assertEqual(result.severity, AnomalySeverity.HIGH)

    def test_missing_current_index(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=None,
            previous_index=100.0,
        )

        self.assertFalse(result.detected)
        self.assertIsNone(result.anomaly_score)

    def test_missing_previous_index(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=105.0,
            previous_index=None,
        )

        self.assertFalse(result.detected)
        self.assertIsNone(result.anomaly_score)

    def test_zero_previous_index(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=105.0,
            previous_index=0.0,
        )

        self.assertFalse(result.detected)
        self.assertIsNone(result.percentage_change)


if __name__ == "__main__":
    unittest.main()