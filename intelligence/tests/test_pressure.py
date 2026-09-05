from intelligence.pressure.scorer import AirfarePressureScorer


def test_low_pressure():
    scorer = AirfarePressureScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        percentage_change=2.0,
        anomaly_score=10.0,
        cross_source_agreement=0.5,
    )

    assert result.pressure_score is not None
    assert 0 <= result.pressure_score <= 100
    assert result.pressure_level in {
        "LOW",
        "MODERATE",
        "HIGH",
        "VERY_HIGH",
    }


def test_high_pressure():
    scorer = AirfarePressureScorer()

    result = scorer.calculate(
        route="DEL-BOM",
        booking_window="T+7",
        percentage_change=20.0,
        anomaly_score=100.0,
        cross_source_agreement=1.0,
    )

    assert result.pressure_score == 100.0
    assert result.pressure_level == "VERY_HIGH"


def test_negative_movement_uses_magnitude():
    scorer = AirfarePressureScorer()

    result = scorer.calculate(
        route="DEL-BLR",
        booking_window="T+15",
        percentage_change=-10.0,
        anomaly_score=50.0,
        cross_source_agreement=0.75,
    )

    assert result.pressure_score > 0
    assert result.percentage_change == -10.0


def test_missing_movement():
    scorer = AirfarePressureScorer()

    result = scorer.calculate(
        route="BOM-BLR",
        booking_window="T+30",
        percentage_change=None,
    )

    assert result.pressure_score is None
    assert result.pressure_level == "INSUFFICIENT_DATA"


def test_score_is_bounded():
    scorer = AirfarePressureScorer()

    result = scorer.calculate(
        route="DEL-CCU",
        booking_window="T+45",
        percentage_change=100.0,
        anomaly_score=500.0,
        cross_source_agreement=2.0,
    )

    assert result.pressure_score == 100.0


def test_to_dict():
    scorer = AirfarePressureScorer()

    result = scorer.calculate(
        route="BLR-HYD",
        booking_window="T+1",
        percentage_change=8.0,
        anomaly_score=40.0,
        cross_source_agreement=0.75,
    )

    data = result.to_dict()

    assert data["route"] == "BLR-HYD"
    assert data["booking_window"] == "T+1"
    assert "pressure_score" in data
    assert "pressure_level" in data