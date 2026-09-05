import pytest

from intelligence.anomaly.detector import AnomalyDetector
from intelligence.evaluation.evaluator import evaluate_detector
from intelligence.shocks.detector import ShockDetector


# ============================================================
# ANOMALY DETECTOR EVALUATION
# ============================================================


def run_anomaly_scenarios():
    """
    Controlled labelled scenarios for AnomalyDetector.

    These are synthetic evaluation labels only.
    They are not real-world airfare ground truth.
    """

    detector = AnomalyDetector()

    scenarios = [
        # Clearly normal upward movement
        {
            "current": 100.2,
            "previous": 100.0,
            "expected": False,
        },

        # Clearly normal downward movement
        {
            "current": 99.5,
            "previous": 100.0,
            "expected": False,
        },

        # Clearly anomalous upward movement
        {
            "current": 105.0,
            "previous": 100.0,
            "expected": True,
        },

        # Clearly anomalous upward movement
        {
            "current": 110.0,
            "previous": 100.0,
            "expected": True,
        },

        # Clearly anomalous high upward movement
        {
            "current": 120.0,
            "previous": 100.0,
            "expected": True,
        },

        # Clearly anomalous downward movement
        {
            "current": 95.0,
            "previous": 100.0,
            "expected": True,
        },

        # Clearly anomalous downward movement
        {
            "current": 90.0,
            "previous": 100.0,
            "expected": True,
        },

        # Clearly anomalous high downward movement
        {
            "current": 80.0,
            "previous": 100.0,
            "expected": True,
        },
    ]

    actual = []
    predicted = []

    for index, scenario in enumerate(scenarios):

        result = detector.detect(
            route=f"TEST-ROUTE-{index}",
            booking_window="T+7",
            current_index=scenario["current"],
            previous_index=scenario["previous"],
        )

        actual.append(scenario["expected"])
        predicted.append(result.detected)

    return actual, predicted


def test_anomaly_detector_synthetic_evaluation():

    actual, predicted = run_anomaly_scenarios()

    result = evaluate_detector(
        detector="AnomalyDetector",
        actual=actual,
        predicted=predicted,
        repeated_predictions=predicted,
        dataset_version="synthetic-anomaly-v1",
    )

    assert result.sample_count == 8
    assert result.evaluation_type == "synthetic_labelled"
    assert result.dataset_version == "synthetic-anomaly-v1"

    assert result.metrics.precision == pytest.approx(1.0)
    assert result.metrics.recall == pytest.approx(1.0)
    assert result.metrics.f1_score == pytest.approx(1.0)
    assert result.metrics.false_positive_rate == pytest.approx(0.0)

    assert result.stability == 1.0


# ============================================================
# SHOCK DETECTOR EVALUATION
# ============================================================


def run_shock_scenarios():
    """
    Controlled labelled scenarios for ShockDetector.

    These scenarios test the detector's evidence progression:

        NORMAL
        ACCELERATION
        MULTIPLE_ROUTES
        CROSS_SOURCE_CONFIRMATION
        POTENTIAL_AIRFARE_SHOCK

    These are synthetic evaluation cases only.
    """

    detector = ShockDetector()

    scenarios = [
        # ------------------------------------------------------
        # 1. Normal movement
        # ------------------------------------------------------
        {
            "current": {
                "DEL-BOM": 101.0,
            },
            "previous": {
                "DEL-BOM": 100.0,
            },
            "previous_movements": {
                "DEL-BOM": 1.0,
            },
            "confirmation": [],
            "coverage": 0.95,
            "freshness": 2.0,
            "expected": False,
        },

        # ------------------------------------------------------
        # 2. Large movement on one route only
        # ------------------------------------------------------
        {
            "current": {
                "DEL-BOM": 125.0,
            },
            "previous": {
                "DEL-BOM": 100.0,
            },
            "previous_movements": {
                "DEL-BOM": 5.0,
            },
            "confirmation": [],
            "coverage": 0.95,
            "freshness": 2.0,
            "expected": False,
        },

        # ------------------------------------------------------
        # 3. Multiple affected routes but no confirmation
        # ------------------------------------------------------
        {
            "current": {
                "DEL-BOM": 120.0,
                "BOM-BLR": 118.0,
            },
            "previous": {
                "DEL-BOM": 100.0,
                "BOM-BLR": 100.0,
            },
            "previous_movements": {
                "DEL-BOM": 5.0,
                "BOM-BLR": 4.0,
            },
            "confirmation": [],
            "coverage": 0.95,
            "freshness": 2.0,
            "expected": False,
        },

        # ------------------------------------------------------
        # 4. Multiple affected routes with confirmation
        # ------------------------------------------------------
        {
            "current": {
                "DEL-BOM": 120.0,
                "BOM-BLR": 118.0,
            },
            "previous": {
                "DEL-BOM": 100.0,
                "BOM-BLR": 100.0,
            },
            "previous_movements": {
                "DEL-BOM": 5.0,
                "BOM-BLR": 4.0,
            },
            "confirmation": [
                {
                    "route": "DEL-BOM",
                    "booking_window": "T+7",
                    "confirmed": True,
                    "agreement_ratio": 1.0,
                },
                {
                    "route": "BOM-BLR",
                    "booking_window": "T+7",
                    "confirmed": True,
                    "agreement_ratio": 1.0,
                },
            ],
            "coverage": 0.95,
            "freshness": 2.0,
            "expected": True,
        },
    ]

    actual = []
    predicted = []

    for scenario in scenarios:

        result = detector.detect(
            route_indices=scenario["current"],
            previous_route_indices=scenario["previous"],
            previous_movements=scenario["previous_movements"],
            cross_source_confirmations=scenario["confirmation"],
            coverage_ratio=scenario["coverage"],
            freshness_hours=scenario["freshness"],
        )

        actual.append(scenario["expected"])

        # ShockDetector returns a dictionary.
        # The detector's boolean shock classification is
        # stored under the "detected" key.
        predicted.append(
            bool(result.get("detected", False))
        )

    return actual, predicted


def test_shock_detector_synthetic_evaluation():

    actual, predicted = run_shock_scenarios()

    result = evaluate_detector(
        detector="ShockDetector",
        actual=actual,
        predicted=predicted,
        repeated_predictions=predicted,
        dataset_version="synthetic-shock-v1",
    )

    assert result.sample_count == 4
    assert result.evaluation_type == "synthetic_labelled"
    assert result.dataset_version == "synthetic-shock-v1"

    assert result.metrics.precision == pytest.approx(1.0)
    assert result.metrics.recall == pytest.approx(1.0)
    assert result.metrics.f1_score == pytest.approx(1.0)
    assert result.metrics.false_positive_rate == pytest.approx(0.0)

    assert result.stability == 1.0