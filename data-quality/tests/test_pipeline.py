from datetime import date, datetime

from src.data_quality.models import (
    RawFareObservation,
    QualityStatus,
)
from src.data_quality.pipeline import (
    process_observation,
    run_pipeline,
)


def make_observation(
    timestamp=datetime(2026, 8, 20, 10, 0),
    source="TEST",
    fare=5300,
    status=None,
):
    return RawFareObservation(
        observation_timestamp=timestamp,
        origin="DEL",
        destination="BOM",
        travel_date=date(2026, 8, 27),
        observation_date=date(2026, 8, 20),
        booking_window="T+7",
        airline="INDIGO",
        flight_number="6E123",
        departure_time="10:30",
        cabin_class="ECONOMY",
        fare_type="STANDARD",
        baggage_characteristics="15KG",
        base_fare=fare - 800,
        taxes=700,
        mandatory_charges=100,
        total_fare=fare,
        source=source,
        observation_status=status,
    )


def test_process_valid_observation():
    observation = make_observation()

    normalized, rejected = process_observation(
        observation
    )

    assert normalized is not None
    assert rejected is None
    assert normalized.origin == "DEL"
    assert normalized.destination == "BOM"
    assert normalized.comparable_fare == 5300
    assert normalized.quality_status == QualityStatus.VALID


def test_invalid_observation_is_rejected():
    observation = make_observation()
    observation.origin = None

    normalized, rejected = process_observation(
        observation
    )

    assert normalized is None
    assert rejected is observation


def test_cancelled_observation_is_rejected():
    observation = make_observation(
        status="CANCELLED"
    )

    normalized, rejected = process_observation(
        observation
    )

    assert normalized is None
    assert rejected is observation


def test_pipeline_processes_multiple_observations():
    observations = [
        make_observation(
            timestamp=datetime(2026, 8, 20, 10, 0),
            fare=5300,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 11, 0),
            fare=5400,
        ),
    ]

    result = run_pipeline(observations)

    assert result.total_processed == 2
    assert len(result.normalized_observations) == 2
    assert result.valid_count == 2


def test_pipeline_detects_duplicate():
    observations = [
        make_observation(
            timestamp=datetime(2026, 8, 20, 10, 0)
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 10, 0)
        ),
    ]

    result = run_pipeline(observations)

    assert len(result.normalized_observations) == 2
    assert result.normalized_observations[
        0
    ].quality_status == QualityStatus.VALID

    assert result.normalized_observations[
        1
    ].quality_status == QualityStatus.EXCLUDED

    assert (
        result.normalized_observations[1].quality_reason
        == "exact duplicate observation"
    )


def test_pipeline_detects_outlier():
    observations = [
        make_observation(fare=5000),
        make_observation(
            timestamp=datetime(2026, 8, 20, 11, 0),
            fare=5100,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 12, 0),
            fare=5200,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 13, 0),
            fare=5300,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 14, 0),
            fare=5400,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 15, 0),
            fare=5500,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 16, 0),
            fare=20000,
        ),
    ]

    result = run_pipeline(observations)

    assert len(result.normalized_observations) == 7
    assert result.outlier_count == 1

    assert (
        result.normalized_observations[6]
        .quality_status
        == QualityStatus.OUTLIER
    )


def test_pipeline_keeps_rejected_records_separately():
    observations = [
        make_observation(),
        make_observation(),
    ]

    observations[1].travel_date = None

    result = run_pipeline(observations)

    assert result.total_processed == 2
    assert len(result.normalized_observations) == 1
    assert len(result.rejected_observations) == 1
    assert result.excluded_count == 1


def test_pipeline_does_not_delete_outlier():
    observations = [
        make_observation(fare=5000),
        make_observation(
            timestamp=datetime(2026, 8, 20, 11, 0),
            fare=5100,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 12, 0),
            fare=5200,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 13, 0),
            fare=5300,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 14, 0),
            fare=5400,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 15, 0),
            fare=5500,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 16, 0),
            fare=20000,
        ),
    ]

    result = run_pipeline(observations)

    assert len(result.normalized_observations) == 7
def test_excluded_observations_do_not_affect_outlier_detection():
    observations = [
        make_observation(fare=5000),
        make_observation(
            timestamp=datetime(2026, 8, 20, 11, 0),
            fare=5100,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 12, 0),
            fare=5200,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 13, 0),
            fare=5300,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 14, 0),
            fare=5400,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 15, 0),
            fare=5500,
        ),
        make_observation(
            timestamp=datetime(2026, 8, 20, 16, 0),
            fare=20000,
        ),
    ]

    # Add an exact duplicate of the first observation.
    # It will be EXCLUDED before outlier detection.
    observations.append(
        make_observation(
            timestamp=datetime(2026, 8, 20, 10, 0),
            fare=5000,
        )
    )

    result = run_pipeline(observations)

    # The duplicate is retained but excluded.
    assert len(result.normalized_observations) == 8
    assert (
        result.normalized_observations[7].quality_status
        == QualityStatus.EXCLUDED
    )

    # The valid observations still produce exactly one outlier.
    assert result.outlier_count == 1
    assert (
        result.normalized_observations[6].quality_status
        == QualityStatus.OUTLIER
    )    