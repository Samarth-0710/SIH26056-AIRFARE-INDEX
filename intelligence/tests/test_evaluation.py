import pytest

from intelligence.evaluation.evaluator import (
    calculate_detection_delay,
    calculate_stability,
    evaluate_classification,
    evaluate_detector,
)


def test_classification_metrics():
    actual = [
        False,
        True,
        True,
        False,
        False,
    ]

    predicted = [
        False,
        True,
        False,
        False,
        True,
    ]

    result = evaluate_classification(
        actual=actual,
        predicted=predicted,
    )

    assert result.true_positive == 1
    assert result.true_negative == 2
    assert result.false_positive == 1
    assert result.false_negative == 1

    assert result.precision == pytest.approx(0.5)
    assert result.recall == pytest.approx(0.5)
    assert result.f1_score == pytest.approx(0.5)
    assert result.false_positive_rate == pytest.approx(1 / 3)


def test_perfect_classification():
    actual = [
        False,
        True,
        False,
        True,
    ]

    predicted = [
        False,
        True,
        False,
        True,
    ]

    result = evaluate_classification(
        actual,
        predicted,
    )

    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1_score == 1.0
    assert result.false_positive_rate == 0.0


def test_detection_delay():
    actual = [
        False,
        True,
        True,
        True,
    ]

    predicted = [
        False,
        False,
        True,
        True,
    ]

    assert calculate_detection_delay(
        actual,
        predicted,
    ) == 1


def test_detection_delay_zero():
    actual = [
        False,
        True,
        True,
    ]

    predicted = [
        False,
        True,
        True,
    ]

    assert calculate_detection_delay(
        actual,
        predicted,
    ) == 0


def test_detection_delay_when_not_detected():
    actual = [
        False,
        True,
        True,
    ]

    predicted = [
        False,
        False,
        False,
    ]

    assert calculate_detection_delay(
        actual,
        predicted,
    ) is None


def test_no_positive_event():
    actual = [
        False,
        False,
        False,
    ]

    predicted = [
        False,
        False,
        False,
    ]

    assert calculate_detection_delay(
        actual,
        predicted,
    ) is None


def test_stability():
    predictions_a = [
        False,
        True,
        True,
        False,
    ]

    predictions_b = [
        False,
        True,
        False,
        False,
    ]

    assert calculate_stability(
        predictions_a,
        predictions_b,
    ) == pytest.approx(0.75)


def test_perfect_stability():
    predictions = [
        False,
        True,
        False,
        True,
    ]

    assert calculate_stability(
        predictions,
        predictions,
    ) == 1.0


def test_evaluate_detector():
    actual = [
        False,
        True,
        True,
        False,
    ]

    predicted = [
        False,
        True,
        False,
        False,
    ]

    result = evaluate_detector(
        detector="anomaly",
        actual=actual,
        predicted=predicted,
        repeated_predictions=predicted,
        dataset_version="synthetic-v1",
    )

    assert result.detector == "anomaly"
    assert result.sample_count == 4
    assert result.dataset_version == "synthetic-v1"
    assert result.evaluation_type == "synthetic_labelled"

    assert result.metrics.recall == pytest.approx(0.5)
    assert result.detection_delay == 0
    assert result.stability == 1.0


def test_length_mismatch():
    with pytest.raises(ValueError):
        evaluate_classification(
            [True],
            [True, False],
        )


def test_empty_classification():
    with pytest.raises(ValueError):
        evaluate_classification(
            [],
            [],
        )


def test_empty_stability():
    with pytest.raises(ValueError):
        calculate_stability(
            [],
            [],
        )