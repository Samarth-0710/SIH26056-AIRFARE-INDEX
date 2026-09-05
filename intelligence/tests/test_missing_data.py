from intelligence.missing_data.supporter import (
    MissingDataSupporter,
)


def test_missing_data_estimate_with_enough_observations():
    supporter = MissingDataSupporter(
        minimum_observations=3
    )

    result = supporter.estimate(
        route="DEL-BOM",
        booking_window="T+7",
        comparable_fares=[5000, 5200, 5100],
    )

    assert result.estimated_fare == 5100
    assert result.comparable_observations == 3
    assert result.used is True
    assert result.confidence == "MODERATE"

    assert result.original_value_missing is True
    assert result.estimated is True
    assert result.estimation_method == "MEDIAN"


def test_missing_data_high_confidence():
    supporter = MissingDataSupporter(
        minimum_observations=3
    )

    result = supporter.estimate(
        route="DEL-BLR",
        booking_window="T+15",
        comparable_fares=[
            5000,
            5100,
            5200,
            5150,
            5050,
        ],
    )

    assert result.estimated_fare == 5100
    assert result.confidence == "HIGH"
    assert result.estimated is True
    assert result.estimation_method == "MEDIAN"


def test_missing_data_insufficient_observations():
    supporter = MissingDataSupporter(
        minimum_observations=3
    )

    result = supporter.estimate(
        route="BOM-BLR",
        booking_window="T+30",
        comparable_fares=[5000, 5200],
    )

    assert result.estimated_fare is None
    assert result.used is False
    assert result.confidence == "INSUFFICIENT_DATA"

    assert result.original_value_missing is True
    assert result.estimated is False
    assert result.estimation_method is None


def test_invalid_fares_are_ignored():
    supporter = MissingDataSupporter(
        minimum_observations=3
    )

    result = supporter.estimate(
        route="DEL-CCU",
        booking_window="T+45",
        comparable_fares=[
            5000,
            -100,
            0,
            None,
            "invalid",
            5200,
            5100,
        ],
    )

    assert result.estimated_fare == 5100
    assert result.comparable_observations == 3
    assert result.used is True
    assert result.estimated is True


def test_median_handles_outlier():
    supporter = MissingDataSupporter(
        minimum_observations=3
    )

    result = supporter.estimate(
        route="BLR-HYD",
        booking_window="T+1",
        comparable_fares=[
            5000,
            5100,
            100000,
        ],
    )

    assert result.estimated_fare == 5100
    assert result.estimation_method == "MEDIAN"


def test_to_dict():
    supporter = MissingDataSupporter(
        minimum_observations=3
    )

    result = supporter.estimate(
        route="MAA-DEL",
        booking_window="T+7",
        comparable_fares=[
            5000,
            5100,
            5200,
        ],
    )

    data = result.to_dict()

    assert data["route"] == "MAA-DEL"
    assert data["booking_window"] == "T+7"
    assert "estimated_fare" in data
    assert "confidence" in data
    assert "used" in data

    assert data["original_value_missing"] is True
    assert data["estimated"] is True
    assert data["estimation_method"] == "MEDIAN"


def test_estimate_is_not_actual_fare():
    supporter = MissingDataSupporter(
        minimum_observations=3
    )

    result = supporter.estimate(
        route="DEL-BOM",
        booking_window="T+7",
        comparable_fares=[
            5000,
            5100,
            5200,
        ],
    )

    assert result.estimated is True
    assert result.original_value_missing is True
    assert result.estimation_method == "MEDIAN"

    # The supporter only produces supporting information.
    # It does not expose the estimate as an actual observation.
    assert result.estimated_fare == 5100