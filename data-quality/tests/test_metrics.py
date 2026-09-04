from datetime import date, datetime

from src.data_quality.models import (
    BookingWindow,
    NormalizedFareObservation,
    QualityStatus,
)
from src.data_quality.metrics import (
    calculate_average_freshness_minutes,
    calculate_booking_window_coverage,
    calculate_freshness_minutes,
    calculate_route_coverage,
    calculate_source_coverage,
    calculate_validity_rate,
    count_quality_statuses,
)


def make_observation(
    route_origin="DEL",
    route_destination="BOM",
    source="SOURCE_A",
    window=BookingWindow.T_7,
    status=QualityStatus.VALID,
    timestamp=datetime(2026, 8, 20, 10, 0),
):
    return NormalizedFareObservation(
        origin=route_origin,
        destination=route_destination,
        travel_date=date(2026, 8, 27),
        observation_date=date(2026, 8, 20),
        booking_window=window,
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
        fingerprint="TEST-FINGERPRINT",
        quality_status=status,
    )


def test_route_coverage():
    observations = [
        make_observation("DEL", "BOM"),
        make_observation("DEL", "BLR"),
    ]

    expected_routes = {
        "DEL-BOM",
        "DEL-BLR",
        "BOM-BLR",
        "BLR-HYD",
    }

    coverage = calculate_route_coverage(
        observations,
        expected_routes,
    )

    assert coverage == 0.5


def test_route_coverage_with_no_expected_routes():
    observations = [make_observation()]

    assert calculate_route_coverage(
        observations,
        set(),
    ) == 0.0


def test_source_coverage():
    observations = [
        make_observation(source="SOURCE_A"),
        make_observation(source="SOURCE_B"),
    ]

    expected_sources = {
        "SOURCE_A",
        "SOURCE_B",
        "SOURCE_C",
        "SOURCE_D",
    }

    coverage = calculate_source_coverage(
        observations,
        expected_sources,
    )

    assert coverage == 0.5


def test_booking_window_coverage():
    observations = [
        make_observation(window=BookingWindow.T_1),
        make_observation(window=BookingWindow.T_7),
        make_observation(window=BookingWindow.T_15),
    ]

    coverage = calculate_booking_window_coverage(
        observations
    )

    assert coverage == 0.6


def test_quality_status_counts():
    observations = [
        make_observation(status=QualityStatus.VALID),
        make_observation(status=QualityStatus.VALID),
        make_observation(status=QualityStatus.EXCLUDED),
        make_observation(status=QualityStatus.OUTLIER),
        make_observation(status=QualityStatus.SUSPECT),
    ]

    counts = count_quality_statuses(observations)

    assert counts["VALID"] == 2
    assert counts["EXCLUDED"] == 1
    assert counts["OUTLIER"] == 1
    assert counts["SUSPECT"] == 1


def test_validity_rate():
    observations = [
        make_observation(status=QualityStatus.VALID),
        make_observation(status=QualityStatus.VALID),
        make_observation(status=QualityStatus.EXCLUDED),
        make_observation(status=QualityStatus.OUTLIER),
    ]

    rate = calculate_validity_rate(observations)

    assert rate == 0.5


def test_validity_rate_with_no_observations():
    assert calculate_validity_rate([]) == 0.0


def test_freshness_minutes():
    observation = make_observation(
        timestamp=datetime(2026, 8, 20, 10, 0)
    )

    current_time = datetime(2026, 8, 20, 11, 30)

    freshness = calculate_freshness_minutes(
        observation,
        current_time,
    )

    assert freshness == 90.0


def test_average_freshness_minutes():
    observations = [
        make_observation(
            timestamp=datetime(2026, 8, 20, 10, 0)
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 11, 0)
        ),
    ]

    current_time = datetime(2026, 8, 20, 12, 0)

    average = calculate_average_freshness_minutes(
        observations,
        current_time,
    )

    assert average == 90.0


def test_average_freshness_with_no_observations():
    assert calculate_average_freshness_minutes(
        [],
        datetime(2026, 8, 20, 12, 0),
    ) == 0.0