import unittest

from intelligence.orchestrator import IntelligenceOrchestrator
from intelligence.models.result import (
    IntelligenceStatus,
    IntelligenceProvenance,
)
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
                "DEL-BOM": [
                    100.0,
                    102.0,
                    104.0,
                    106.0,
                    108.0,
                ],
                "DEL-BLR": [
                    100.0,
                    100.5,
                    101.0,
                ],
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

        self.assertTrue(
            anomaly.detected
        )

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

        self.assertIn(
            "DEL-BOM",
            patterns,
        )

        self.assertEqual(
            patterns["DEL-BOM"]["pattern"],
            PatternType.UPWARD,
        )

        self.assertTrue(
            patterns["DEL-BOM"]["detected"]
        )

    def test_shock_detection_is_included(self):
        """
        The enhanced shock detector requires multiple
        independent supporting signals before declaring a
        potential airfare shock.

        Required signals:
        - significant movement
        - multiple affected routes
        - cross-source confirmation
        - adequate coverage
        - fresh observations
        """

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
            coverage_ratio=1.0,
            freshness_hours=2.0,
            current_observations=[
                {
                    "origin": "DEL",
                    "destination": "BOM",
                    "booking_window": "T+7",
                    "observation_date": "2026-09-04",
                    "source": "SOURCE_A",
                    "comparable_fare": 12500.0,
                },
                {
                    "origin": "DEL",
                    "destination": "BOM",
                    "booking_window": "T+7",
                    "observation_date": "2026-09-04",
                    "source": "SOURCE_B",
                    "comparable_fare": 12600.0,
                },
                {
                    "origin": "DEL",
                    "destination": "BLR",
                    "booking_window": "T+7",
                    "observation_date": "2026-09-04",
                    "source": "SOURCE_A",
                    "comparable_fare": 11000.0,
                },
                {
                    "origin": "DEL",
                    "destination": "BLR",
                    "booking_window": "T+7",
                    "observation_date": "2026-09-04",
                    "source": "SOURCE_B",
                    "comparable_fare": 11100.0,
                },
            ],
            previous_observations=[
                {
                    "origin": "DEL",
                    "destination": "BOM",
                    "booking_window": "T+7",
                    "observation_date": "2026-09-03",
                    "source": "SOURCE_A",
                    "comparable_fare": 10000.0,
                },
                {
                    "origin": "DEL",
                    "destination": "BOM",
                    "booking_window": "T+7",
                    "observation_date": "2026-09-03",
                    "source": "SOURCE_B",
                    "comparable_fare": 10100.0,
                },
                {
                    "origin": "DEL",
                    "destination": "BLR",
                    "booking_window": "T+7",
                    "observation_date": "2026-09-03",
                    "source": "SOURCE_A",
                    "comparable_fare": 10000.0,
                },
                {
                    "origin": "DEL",
                    "destination": "BLR",
                    "booking_window": "T+7",
                    "observation_date": "2026-09-03",
                    "source": "SOURCE_B",
                    "comparable_fare": 10100.0,
                },
            ],
        )

        shock = result.metadata["shock"]

        self.assertTrue(
            shock["detected"]
        )

        self.assertEqual(
            shock["severity"],
            ShockSeverity.HIGH,
        )

        self.assertEqual(
            shock["stage"],
            "POTENTIAL_AIRFARE_SHOCK",
        )

        self.assertEqual(
            set(shock["affected_routes"]),
            {
                "DEL-BOM",
                "DEL-BLR",
            },
        )

        self.assertTrue(
            shock["cross_source_confirmed"]
        )

        self.assertEqual(
            set(shock["cross_source_confirmed_routes"]),
            {
                "DEL-BOM",
                "DEL-BLR",
            },
        )

        self.assertEqual(
            shock["coverage_ratio"],
            1.0,
        )

        self.assertEqual(
            shock["freshness_hours"],
            2.0,
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
        for window in [
            "T+1",
            "T+7",
            "T+15",
            "T+30",
            "T+45",
        ]:

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

    def test_default_intelligence_provenance(self):
        provenance = IntelligenceProvenance()

        data = provenance.to_dict()

        self.assertEqual(
            data["model_version"],
            "intelligence-rules-v1",
        )

        self.assertEqual(
            data["feature_version"],
            "features-v1",
        )

        self.assertEqual(
            data["training_dataset_version"],
            "NOT_APPLICABLE",
        )

        self.assertEqual(
            data["reference_dataset_version"],
            "NOT_APPLICABLE",
        )

        self.assertIsNone(
            data["generated_at"]
        )

        self.assertIsInstance(
            data["configuration"],
            dict,
        )

    def test_custom_intelligence_provenance(self):
        provenance = IntelligenceProvenance(
            model_version="intelligence-rules-v2",
            feature_version="features-v2",
            training_dataset_version="NOT_APPLICABLE",
            reference_dataset_version="reference-2026-09",
            generated_at="2026-09-05T10:00:00",
            configuration={
                "anomaly_threshold_high": 10.0,
                "shock_threshold_high": 20.0,
            },
        )

        data = provenance.to_dict()

        self.assertEqual(
            data["model_version"],
            "intelligence-rules-v2",
        )

        self.assertEqual(
            data["feature_version"],
            "features-v2",
        )

        self.assertEqual(
            data["training_dataset_version"],
            "NOT_APPLICABLE",
        )

        self.assertEqual(
            data["reference_dataset_version"],
            "reference-2026-09",
        )

        self.assertEqual(
            data["generated_at"],
            "2026-09-05T10:00:00",
        )

        self.assertEqual(
            data["configuration"][
                "anomaly_threshold_high"
            ],
            10.0,
        )

        self.assertEqual(
            data["configuration"][
                "shock_threshold_high"
            ],
            20.0,
        )


if __name__ == "__main__":
    unittest.main()