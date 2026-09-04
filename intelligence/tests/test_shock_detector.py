import unittest

from intelligence.shocks.detector import (
    ShockDetector,
    ShockSeverity,
)


class TestShockDetector(unittest.TestCase):

    def setUp(self):
        self.detector = ShockDetector()

    def test_no_shock(self):
        result = self.detector.detect(
            route_indices={
                "DEL-BOM": 101.0,
                "DEL-BLR": 102.0,
                "BOM-BLR": 101.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
        )

        self.assertFalse(result["detected"])
        self.assertEqual(
            result["severity"],
            ShockSeverity.NONE,
        )

    def test_low_shock(self):
        result = self.detector.detect(
            route_indices={
                "DEL-BOM": 106.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
        )

        self.assertTrue(result["detected"])
        self.assertEqual(
            result["severity"],
            ShockSeverity.LOW,
        )

        self.assertIn(
            "DEL-BOM",
            result["affected_routes"],
        )

    def test_medium_shock(self):
        result = self.detector.detect(
            route_indices={
                "DEL-BOM": 112.0,
                "DEL-BLR": 105.0,
                "BOM-BLR": 100.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
        )

        self.assertTrue(result["detected"])
        self.assertEqual(
            result["severity"],
            ShockSeverity.MEDIUM,
        )

    def test_high_shock(self):
        result = self.detector.detect(
            route_indices={
                "DEL-BOM": 125.0,
                "DEL-BLR": 110.0,
                "BOM-BLR": 100.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
        )

        self.assertTrue(result["detected"])
        self.assertEqual(
            result["severity"],
            ShockSeverity.HIGH,
        )

    def test_downward_shock(self):
        result = self.detector.detect(
            route_indices={
                "DEL-BOM": 80.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
        )

        self.assertTrue(result["detected"])
        self.assertEqual(
            result["severity"],
            ShockSeverity.HIGH,
        )

    def test_missing_route_data(self):
        result = self.detector.detect(
            route_indices={
                "DEL-BOM": None,
                "DEL-BLR": 101.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
            },
        )

        self.assertFalse(result["detected"])
        self.assertAlmostEqual(
            result["average_movement"],
            1.0,
        )

    def test_empty_data(self):
        result = self.detector.detect(
            route_indices={},
            previous_route_indices={},
        )

        self.assertFalse(result["detected"])
        self.assertEqual(
            result["severity"],
            ShockSeverity.NONE,
        )

    def test_multiple_affected_routes(self):
        result = self.detector.detect(
            route_indices={
                "DEL-BOM": 106.0,
                "DEL-BLR": 108.0,
                "BOM-BLR": 102.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
        )

        self.assertIn(
            "DEL-BOM",
            result["affected_routes"],
        )

        self.assertIn(
            "DEL-BLR",
            result["affected_routes"],
        )

        self.assertNotIn(
            "BOM-BLR",
            result["affected_routes"],
        )


if __name__ == "__main__":
    unittest.main()