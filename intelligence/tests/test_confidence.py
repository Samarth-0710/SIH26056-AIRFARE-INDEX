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


def test_source_coverage_signal():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=0.8,
        cross_source_agreement=0.8,
        anomaly_available=True,
        source_coverage=0.9,
    )

    assert result.confidence_score is not None
    assert result.source_coverage == 0.9
    assert 0 <= result.confidence_score <= 100


def test_observation_volume_signal():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=0.8,
        observation_count=8,
        expected_observation_count=10,
    )

    assert result.observation_volume_ratio == 0.8
    assert result.confidence_score is not None
    assert 0 <= result.confidence_score <= 100


def test_observation_volume_is_capped():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=1.0,
        observation_count=20,
        expected_observation_count=10,
    )

    assert result.observation_volume_ratio == 1.0
    assert result.confidence_score is not None
    assert 0 <= result.confidence_score <= 100


def test_data_quality_signal():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=0.9,
        data_quality=0.95,
    )

    assert result.confidence_score is not None
    assert result.data_quality == 0.95
    assert 0 <= result.confidence_score <= 100


def test_freshness_signal():
    scorer = ConfidenceSupportScorer(
        maximum_freshness_hours=48
    )

    fresh = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=0.9,
        freshness_hours=2,
    )

    stale = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=0.9,
        freshness_hours=60,
    )

    assert fresh.confidence_score is not None
    assert stale.confidence_score is not None
    assert fresh.confidence_score > stale.confidence_score


def test_missing_optional_signals_do_not_fail():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=0.75,
    )

    assert result.confidence_score is not None
    assert 0 <= result.confidence_score <= 100


def test_extended_result_to_dict():
    scorer = ConfidenceSupportScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        coverage_ratio=0.9,
        cross_source_agreement=0.8,
        anomaly_available=True,
        source_coverage=0.75,
        observation_count=9,
        expected_observation_count=10,
        data_quality=0.95,
        freshness_hours=4,
    )

    data = result.to_dict()

    assert data["source_coverage"] == 0.75
    assert data["observation_count"] == 9
    assert data["expected_observation_count"] == 10
    assert data["observation_volume_ratio"] == 0.9
    assert data["data_quality"] == 0.95
    assert data["freshness_hours"] == 4