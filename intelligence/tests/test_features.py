from datetime import datetime, timedelta

from intelligence.features.engineer import FareFeatureEngineer


def test_build_basic_features():
    engineer = FareFeatureEngineer()

    result = engineer.build(
        route="DEL-BOM",
        booking_window="T+7",
        current_fare=5500,
        previous_fare=5000,
    )

    assert result.current_fare == 5500
    assert result.previous_fare == 5000
    assert result.percentage_change == 10.0
    assert result.rate_of_change == 10.0


def test_acceleration():
    engineer = FareFeatureEngineer()

    result = engineer.build(
        route="DEL-BLR",
        booking_window="T+15",
        current_fare=6000,
        previous_fare=5000,
        previous_percentage_change=5.0,
    )

    assert result.percentage_change == 20.0
    assert result.acceleration == 15.0


def test_rolling_features():
    engineer = FareFeatureEngineer(rolling_window=5)

    result = engineer.build(
        route="BOM-BLR",
        booking_window="T+30",
        current_fare=6000,
        historical_fares=[
            5000,
            5100,
            5200,
            5300,
            5400,
        ],
    )

    assert result.rolling_mean == 5200
    assert result.rolling_median == 5200
    assert result.rolling_volatility is not None
    assert result.rolling_volatility > 0


def test_rolling_window_limits_history():
    engineer = FareFeatureEngineer(rolling_window=3)

    result = engineer.build(
        route="DEL-CCU",
        booking_window="T+45",
        current_fare=6000,
        historical_fares=[
            1000,
            2000,
            5000,
            6000,
        ],
    )

    assert result.rolling_mean == 4333.33
    assert result.rolling_median == 5000


def test_source_and_observation_features():
    engineer = FareFeatureEngineer()

    observations = [
        {"source": "INDIGO"},
        {"source": "AIR INDIA"},
        {"source": "MAKEMYTRIP"},
    ]

    result = engineer.build(
        route="BLR-HYD",
        booking_window="T+1",
        current_fare=5000,
        current_observations=observations,
        coverage_ratio=0.8,
    )

    assert result.observation_count == 3
    assert result.source_count == 3
    assert result.coverage_ratio == 0.8


def test_cross_source_agreement():
    engineer = FareFeatureEngineer()

    result = engineer.build(
        route="DEL-BOM",
        booking_window="T+7",
        current_fare=5500,
        cross_source_result={
            "agreement_ratio": 0.75,
        },
    )

    assert result.cross_source_agreement == 0.75


def test_freshness():
    engineer = FareFeatureEngineer()

    reference = datetime(2026, 9, 1, 12, 0, 0)
    observed = reference - timedelta(hours=3)

    result = engineer.build(
        route="MAA-DEL",
        booking_window="T+15",
        current_fare=5000,
        observation_timestamp=observed,
        reference_timestamp=reference,
    )

    assert result.freshness_hours == 3.0


def test_missing_values_are_safe():
    engineer = FareFeatureEngineer()

    result = engineer.build(
        route="DEL-BOM",
        booking_window="T+7",
        current_fare=None,
        previous_fare=None,
    )

    assert result.current_fare is None
    assert result.previous_fare is None
    assert result.percentage_change is None
    assert result.acceleration is None


def test_to_dict():
    engineer = FareFeatureEngineer()

    result = engineer.build(
        route="DEL-BOM",
        booking_window="T+7",
        current_fare=5500,
        previous_fare=5000,
    )

    data = result.to_dict()

    assert data["route"] == "DEL-BOM"
    assert data["booking_window"] == "T+7"
    assert "rolling_mean" in data
    assert "acceleration" in data
    assert "freshness_hours" in data
    