import unittest

from intelligence.orchestrator import IntelligenceOrchestrator
from intelligence.models.result import IntelligenceStatus
from intelligence.anomaly.detector import AnomalySeverity
from intelligence.patterns.detector import PatternType
from intelligence.shocks.detector import ShockSeverity


class TestIntelligenceOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orchestrator = IntelligenceOrchestrator()

    def test_analyze_route_indices(self):
        result = self.orchestrator.analyze(
            observation_date="2026-09-04",
            current_route_indices={
                "DEL-BOM": 108.0,
                "DEL-BLR": 101.0,
                "BOM-BLR": 100.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
                "BOM-BLR": 100.0,
            },
            historical_route_indices={
                "DEL-BOM": [100.0, 102.0, 104.0, 106.0, 108.0],
                "DEL-BLR": [100.0, 100.5, 101.0],
            },
            booking_window="T+7",
        )

        self.assertEqual(
            result.status,
            IntelligenceStatus.SUCCESS,
        )

        self.assertEqual(
            result.observation_date,
            "2026-09-04",
        )

        self.assertEqual(
            len(result.anomalies),
            3,
        )

    def test_anomaly_is_explained(self):
        result = self.orchestrator.analyze(
            observation_date="2026-09-04",
            current_route_indices={
                "DEL-BOM": 108.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
            },
            booking_window="T+7",
        )

        anomaly = result.anomalies[0]

        self.assertTrue(anomaly.detected)
        self.assertEqual(
            anomaly.severity,
            AnomalySeverity.MEDIUM,
        )

        self.assertIn(
            "DEL-BOM",
            anomaly.reason,
        )

        self.assertIn(
            "increased",
            anomaly.reason,
        )

    def test_pattern_detection_is_included(self):
        result = self.orchestrator.analyze(
            observation_date="2026-09-04",
            current_route_indices={
                "DEL-BOM": 108.0,
            },
            previous_route_indices={
                "DEL-BOM": 106.0,
            },
            historical_route_indices={
                "DEL-BOM": [
                    100.0,
                    102.0,
                    104.0,
                    106.0,
                    108.0,
                ],
            },
            booking_window="T+7",
        )

        patterns = result.metadata["patterns"]

        self.assertIn("DEL-BOM", patterns)

        self.assertEqual(
            patterns["DEL-BOM"]["pattern"],
            PatternType.UPWARD,
        )

        self.assertTrue(
            patterns["DEL-BOM"]["detected"]
        )

    def test_shock_detection_is_included(self):
        result = self.orchestrator.analyze(
            observation_date="2026-09-04",
            current_route_indices={
                "DEL-BOM": 125.0,
                "DEL-BLR": 110.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
                "DEL-BLR": 100.0,
            },
            booking_window="T+7",
        )

        shock = result.metadata["shock"]

        self.assertTrue(shock["detected"])

        self.assertEqual(
            shock["severity"],
            ShockSeverity.HIGH,
        )

        self.assertIn(
            "DEL-BOM",
            shock["affected_routes"],
        )

    def test_without_historical_data(self):
        result = self.orchestrator.analyze(
            observation_date="2026-09-04",
            current_route_indices={
                "DEL-BOM": 103.0,
            },
            previous_route_indices={
                "DEL-BOM": 100.0,
            },
            booking_window="T+7",
        )

        self.assertEqual(
            result.metadata["patterns"],
            {},
        )

        self.assertFalse(
            result.metadata["shock"]["detected"]
        )

    def test_multiple_booking_windows(self):
        for window in ["T+1", "T+7", "T+15", "T+30", "T+45"]:

            result = self.orchestrator.analyze(
                observation_date="2026-09-04",
                current_route_indices={
                    "DEL-BOM": 108.0,
                },
                previous_route_indices={
                    "DEL-BOM": 100.0,
                },
                booking_window=window,
            )

            self.assertEqual(
                result.anomalies[0].booking_window,
                window,
            )


if __name__ == "__main__":
    unittest.main()