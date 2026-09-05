from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ClassificationMetrics:
    """
    Classification metrics for labelled intelligence scenarios.

    These metrics describe performance on the supplied evaluation
    labels only. They are not claims about production accuracy.
    """

    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int

    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float

    def to_dict(self):
        return {
            "true_positive": self.true_positive,
            "true_negative": self.true_negative,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "false_positive_rate": self.false_positive_rate,
        }


@dataclass(frozen=True)
class EvaluationResult:
    """
    Complete evaluation result for an Intelligence detector.
    """

    detector: str
    metrics: ClassificationMetrics
    detection_delay: Optional[float]
    stability: float
    sample_count: int
    dataset_version: str
    evaluation_type: str = "synthetic_labelled"

    def to_dict(self):
        return {
            "detector": self.detector,
            "metrics": self.metrics.to_dict(),
            "detection_delay": self.detection_delay,
            "stability": self.stability,
            "sample_count": self.sample_count,
            "dataset_version": self.dataset_version,
            "evaluation_type": self.evaluation_type,
        }


def evaluate_classification(
    actual: List[bool],
    predicted: List[bool],
) -> ClassificationMetrics:
    """
    Calculate binary classification metrics.

    Parameters
    ----------
    actual:
        Ground-truth labels.

    predicted:
        Detector predictions.

    Returns
    -------
    ClassificationMetrics
    """

    if len(actual) != len(predicted):
        raise ValueError(
            "actual and predicted must have the same length"
        )

    if not actual:
        raise ValueError(
            "Evaluation requires at least one sample"
        )

    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0

    for expected, result in zip(actual, predicted):

        if expected and result:
            true_positive += 1

        elif not expected and not result:
            true_negative += 1

        elif not expected and result:
            false_positive += 1

        else:
            false_negative += 1

    precision_denominator = (
        true_positive + false_positive
    )

    recall_denominator = (
        true_positive + false_negative
    )

    fpr_denominator = (
        false_positive + true_negative
    )

    precision = (
        true_positive / precision_denominator
        if precision_denominator
        else 0.0
    )

    recall = (
        true_positive / recall_denominator
        if recall_denominator
        else 0.0
    )

    if precision + recall:
        f1_score = (
            2 * precision * recall
            / (precision + recall)
        )
    else:
        f1_score = 0.0

    false_positive_rate = (
        false_positive / fpr_denominator
        if fpr_denominator
        else 0.0
    )

    return ClassificationMetrics(
        true_positive=true_positive,
        true_negative=true_negative,
        false_positive=false_positive,
        false_negative=false_negative,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        false_positive_rate=false_positive_rate,
    )


def calculate_detection_delay(
    actual: List[bool],
    predicted: List[bool],
) -> Optional[int]:
    """
    Calculate detection delay for the first positive event.

    Delay is measured in evaluation steps.

    Example:

        actual    = [False, True, True]
        predicted = [False, False, True]

    Detection delay = 1.

    Returns None when there is no positive event or when it
    is never detected.
    """

    if len(actual) != len(predicted):
        raise ValueError(
            "actual and predicted must have the same length"
        )

    actual_event = None

    for index, value in enumerate(actual):
        if value:
            actual_event = index
            break

    if actual_event is None:
        return None

    for index in range(actual_event, len(predicted)):
        if predicted[index]:
            return index - actual_event

    return None


def calculate_stability(
    predictions_a: List[bool],
    predictions_b: List[bool],
) -> float:
    """
    Measure prediction stability across two repeated runs.

    Stability is the fraction of predictions that remain identical.

    Returns a value between 0 and 1.
    """

    if len(predictions_a) != len(predictions_b):
        raise ValueError(
            "Repeated evaluation runs must have the same length"
        )

    if not predictions_a:
        raise ValueError(
            "Stability requires at least one prediction"
        )

    matching = sum(
        first == second
        for first, second in zip(
            predictions_a,
            predictions_b,
        )
    )

    return matching / len(predictions_a)


def evaluate_detector(
    detector: str,
    actual: List[bool],
    predicted: List[bool],
    repeated_predictions: Optional[List[bool]] = None,
    dataset_version: str = "synthetic-v1",
) -> EvaluationResult:
    """
    Evaluate a detector against labelled scenarios.

    No production accuracy is implied by this function.
    """

    metrics = evaluate_classification(
        actual=actual,
        predicted=predicted,
    )

    delay = calculate_detection_delay(
        actual=actual,
        predicted=predicted,
    )

    if repeated_predictions is None:
        stability = 1.0
    else:
        stability = calculate_stability(
            predictions_a=predicted,
            predictions_b=repeated_predictions,
        )

    return EvaluationResult(
        detector=detector,
        metrics=metrics,
        detection_delay=delay,
        stability=stability,
        sample_count=len(actual),
        dataset_version=dataset_version,
    )