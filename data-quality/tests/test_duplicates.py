from datetime import date, datetime

from src.data_quality.models import (
    NormalizedFareObservation,
    BookingWindow,
    QualityStatus,
)
from src.data_quality.duplicates import (
    find_duplicate_indices,
    count_duplicates,
    mark_duplicates,
)


def make_observation(
    timestamp=datetime(2026, 8, 20, 10, 0),
    source="TEST",
    fingerprint="ABC123",
):
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
        base_fare=4500,
        taxes=700,
        mandatory_charges=100,
        comparable_fare=5300,
        source=source,
        observation_timestamp=timestamp,
        fingerprint=fingerprint,
        quality_status=QualityStatus.VALID,
    )


def test_exact_duplicate_is_detected():
    observations = [
        make_observation(),
        make_observation(),
    ]

    assert find_duplicate_indices(observations) == [1]
    assert count_duplicates(observations) == 1


def test_first_occurrence_is_not_duplicate():
    observations = [
        make_observation(),
        make_observation(),
    ]

    duplicates = find_duplicate_indices(observations)

    assert 0 not in duplicates
    assert 1 in duplicates


def test_same_fare_at_different_time_is_not_duplicate():
    observations = [
        make_observation(
            timestamp=datetime(2026, 8, 20, 10, 0)
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 11, 0)
        ),
    ]

    assert count_duplicates(observations) == 0


def test_same_fare_from_different_source_is_not_duplicate():
    observations = [
        make_observation(source="SOURCE_A"),
        make_observation(source="SOURCE_B"),
    ]

    assert count_duplicates(observations) == 0


def test_different_fingerprint_is_not_duplicate():
    observations = [
        make_observation(fingerprint="ABC123"),
        make_observation(fingerprint="XYZ789"),
    ]

    assert count_duplicates(observations) == 0


def test_mark_duplicates_excludes_only_later_record():
    observations = [
        make_observation(),
        make_observation(),
    ]

    result = mark_duplicates(observations)

    assert result[0].quality_status == QualityStatus.VALID
    assert result[1].quality_status == QualityStatus.EXCLUDED
    assert result[1].quality_reason == "exact duplicate observation"
