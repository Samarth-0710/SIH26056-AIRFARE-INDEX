from intelligence.confidence.scorer import ConfidenceSupportScorer


def test_high_confidence_support():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=1.0,
        cross_source_agreement=1.0,
        anomaly_available=True,
    )

    assert result.confidence_score == 100.0
    assert result.confidence_level == "VERY_HIGH"


def test_low_confidence_support():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=0.2,
        cross_source_agreement=0.0,
        anomaly_available=False,
    )

    assert result.confidence_score == 10.0
    assert result.confidence_level == "LOW"


def test_partial_coverage():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="BLR-HYD",
        booking_window="T+15",
        coverage_ratio=0.6,
        cross_source_agreement=0.75,
        anomaly_available=True,
    )

    assert result.confidence_score is not None
    assert 0 <= result.confidence_score <= 100


def test_missing_coverage():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="BOM-BLR",
        booking_window="T+30",
        coverage_ratio=None,
    )

    assert result.confidence_score is None
    assert result.confidence_level == "INSUFFICIENT_DATA"


def test_score_is_bounded():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-CCU",
        booking_window="T+45",
        coverage_ratio=2.0,
        cross_source_agreement=2.0,
        anomaly_available=True,
    )

    assert result.confidence_score == 100.0


def test_to_dict():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="MAA-DEL",
        booking_window="T+1",
        coverage_ratio=0.8,
        cross_source_agreement=0.75,
        anomaly_available=True,
    )

    data = result.to_dict()

    assert data["route"] == "MAA-DEL"
    assert data["booking_window"] == "T+1"
    assert "confidence_score" in data
    assert "confidence_level" in data