from datetime import date, datetime

from src.data_quality.models import (
    BookingWindow,
    NormalizedFareObservation,
    QualityStatus,
)
from src.data_quality.outliers import (
    calculate_iqr_bounds,
    count_outliers,
    find_outlier_indices,
    mark_outliers,
)


def make_observation(fare):
    return NormalizedFareObservation(
        origin="DEL",
        destination="BOM",
        travel_date=date(2026, 8, 27),
        observation_date=date(2026, 8, 20),
        booking_window=BookingWindow.T_7,
        airline="INDIGO",
        flight_number="6E123",
        departure_time="10:30",
        cabin_class="ECONOMY",
        fare_type="STANDARD",
        baggage_characteristics="15KG",
        base_fare=fare - 800,
        taxes=700,
        mandatory_charges=100,
        comparable_fare=fare,
        source="TEST",
        observation_timestamp=datetime(2026, 8, 20, 10, 0),
        fingerprint=f"FP-{fare}",
        quality_status=QualityStatus.VALID,
    )


def test_iqr_bounds():
    values = [100, 110, 120, 130, 140, 150, 160]

    lower, upper = calculate_iqr_bounds(values)

    assert lower < 100
    assert upper > 160


def test_empty_values_raise_error():
    try:
        calculate_iqr_bounds([])
        assert False
    except ValueError:
        assert True


def test_negative_multiplier_raises_error():
    values = [100, 110, 120]

    try:
        calculate_iqr_bounds(values, multiplier=-1)
        assert False
    except ValueError:
        assert True


def test_too_few_observations_are_not_flagged():
    observations = [
        make_observation(1000),
        make_observation(1100),
        make_observation(1200),
    ]

    assert find_outlier_indices(observations) == []


def test_extreme_fare_is_detected():
    observations = [
        make_observation(5000),
        make_observation(5100),
        make_observation(5200),
        make_observation(5300),
        make_observation(5400),
        make_observation(5500),
        make_observation(20000),
    ]

    outliers = find_outlier_indices(observations)

    assert 6 in outliers


def test_normal_fares_are_not_flagged():
    observations = [
        make_observation(5000),
        make_observation(5100),
        make_observation(5200),
        make_observation(5300),
        make_observation(5400),
        make_observation(5500),
        make_observation(5600),
    ]

    assert count_outliers(observations) == 0


def test_outlier_is_marked_without_deleting_it():
    observations = [
        make_observation(5000),
        make_observation(5100),
        make_observation(5200),
        make_observation(5300),
        make_observation(5400),
        make_observation(5500),
        make_observation(20000),
    ]

    result = mark_outliers(observations)

    assert len(result) == 7
    assert result[6].quality_status == QualityStatus.OUTLIER
    assert "IQR outlier" in result[6].quality_reason


def test_missing_fare_is_ignored():
    observations = [
        make_observation(5000),
        make_observation(5100),
        make_observation(5200),
        make_observation(5300),
        make_observation(5400),
        make_observation(5500),
    ]

    observations.append(
        NormalizedFareObservation(
            origin="DEL",
            destination="BOM",
            travel_date=date(2026, 8, 27),
            observation_date=date(2026, 8, 20),
            booking_window=BookingWindow.T_7,
            airline="INDIGO",
            flight_number="6E123",
            departure_time="10:30",
            cabin_class="ECONOMY",
            fare_type="STANDARD",
            baggage_characteristics="15KG",
            base_fare=None,
            taxes=None,
            mandatory_charges=None,
            comparable_fare=None,
            source="TEST",
            observation_timestamp=datetime(
                2026, 8, 20, 10, 0
            ),
            fingerprint="MISSING",
            quality_status=QualityStatus.EXCLUDED,
        )
    )

    assert count_outliers(observations) == 0