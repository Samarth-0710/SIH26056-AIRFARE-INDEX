import unittest

from intelligence.anomaly.detector import AnomalyDetector
from intelligence.explainability.explainer import AnomalyExplainer


class TestAnomalyExplainer(unittest.TestCase):

    def setUp(self):
        self.detector = AnomalyDetector()
        self.explainer = AnomalyExplainer()

    def test_explain_detected_anomaly(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=108.0,
            previous_index=100.0,
        )

        explanation = self.explainer.explain(result)

        self.assertIn("DEL-BOM", explanation)
        self.assertIn("T+7", explanation)
        self.assertIn("increased", explanation)
        self.assertIn("8.00%", explanation)
        self.assertIn("MEDIUM", explanation)

    def test_explain_normal_result(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=101.0,
            previous_index=100.0,
        )

        explanation = self.explainer.explain(result)

        self.assertIn("No significant anomaly", explanation)

    def test_explain_decrease(self):
        result = self.detector.detect(
            route="DEL-BOM",
            booking_window="T+7",
            current_index=90.0,
            previous_index=100.0,
        )

        explanation = self.explainer.explain(result)

        self.assertIn("decreased", explanation)
        self.assertIn("10.00%", explanation)


if __name__ == "__main__":
    unittest.main()