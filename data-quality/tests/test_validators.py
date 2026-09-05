from datetime import date, datetime

from src.data_quality.models import RawFareObservation, QualityStatus
from src.data_quality.validators import (
    classify_raw_observation,
    has_required_data,
    validate_normalized_observation,
)
from datetime import date, datetime

from data_quality.models import QualityStatus, RawFareObservation
from data_quality.validators import (
    CANCELLED,
    MISSING_FARE,
    MISSING_SOURCE,
    SOLD_OUT,
    UNKNOWN_SOURCE,
    UNAVAILABLE,
    classify_raw_observation,
)


def make_raw_observation(**overrides):
    data = {
        "observation_timestamp": datetime(
            2026, 9, 1, 10, 0
        ),
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": date(2026, 9, 8),
        "observation_date": date(2026, 9, 1),
        "airline": "IndiGo",
        "flight_number": "6E123",
        "departure_time": "10:30",
        "cabin_class": "Economy",
        "fare_type": "Regular",
        "baggage_characteristics": "15KG",
        "base_fare": 4500,
        "taxes": 700,
        "mandatory_charges": 100,
        "source": "MMT",
    }

    data.update(overrides)

    return RawFareObservation(**data)


def test_sold_out_is_excluded():
    status, reason = classify_raw_observation(
        make_raw_observation(
            observation_status="SOLD OUT"
        )
    )

    assert status == QualityStatus.EXCLUDED
    assert reason == SOLD_OUT


def test_cancelled_is_excluded():
    status, reason = classify_raw_observation(
        make_raw_observation(
            observation_status="CANCELLED"
        )
    )

    assert status == QualityStatus.EXCLUDED
    assert reason == CANCELLED


def test_unavailable_is_excluded():
    status, reason = classify_raw_observation(
        make_raw_observation(
            observation_status="UNAVAILABLE"
        )
    )

    assert status == QualityStatus.EXCLUDED
    assert reason == UNAVAILABLE


def test_missing_fare_is_excluded():
    status, reason = classify_raw_observation(
        make_raw_observation(
            base_fare=None
        )
    )

    assert status == QualityStatus.EXCLUDED
    assert MISSING_FARE in reason


def test_missing_source_is_excluded():
    status, reason = classify_raw_observation(
        make_raw_observation(
            source=None
        )
    )

    assert status == QualityStatus.EXCLUDED
    assert MISSING_SOURCE in reason


def test_unknown_source_is_excluded():
    status, reason = classify_raw_observation(
        make_raw_observation(
            source="UNKNOWN-FLIGHT-SITE"
        )
    )

    assert status == QualityStatus.EXCLUDED
    assert UNKNOWN_SOURCE in reason

def make_valid_observation():
    return RawFareObservation(
        observation_timestamp=datetime(2026, 8, 20, 10, 0),
        origin="DEL",
        destination="BOM",
        travel_date=date(2026, 8, 27),
        observation_date=date(2026, 8, 20),
        booking_window="T+7",
        airline="IndiGo",
        flight_number="6E123",
        departure_time="10:30",
        cabin_class="ECONOMY",
        fare_type="STANDARD",
        baggage_characteristics="15KG",
        base_fare=4500,
        taxes=700,
        mandatory_charges=100,
        total_fare=5300,
        source="TEST",
    )


def test_valid_observation():
    observation = make_valid_observation()

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.VALID
    assert reason == ""


def test_missing_origin():
    observation = make_valid_observation()
    observation.origin = None

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "missing origin" in reason


def test_missing_destination():
    observation = make_valid_observation()
    observation.destination = None

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "missing destination" in reason


def test_missing_airline():
    observation = make_valid_observation()
    observation.airline = None

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "missing airline" in reason


def test_missing_travel_date():
    observation = make_valid_observation()
    observation.travel_date = None

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "missing travel date" in reason


def test_negative_base_fare():
    observation = make_valid_observation()
    observation.base_fare = -100

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "negative base fare" in reason


def test_missing_taxes():
    observation = make_valid_observation()
    observation.taxes = None

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "missing taxes" in reason


def test_missing_mandatory_charges():
    observation = make_valid_observation()
    observation.mandatory_charges = None

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "missing mandatory charges" in reason


def test_cancelled_flight():
    observation = make_valid_observation()
    observation.observation_status = "CANCELLED"

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "cancelled flight" in reason


def test_sold_out_observation():
    observation = make_valid_observation()
    observation.observation_status = "SOLD_OUT"

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "sold-out observation" in reason


def test_travel_date_before_observation_date():
    observation = make_valid_observation()
    observation.travel_date = date(2026, 8, 19)

    status, reason = classify_raw_observation(observation)

    assert status == QualityStatus.EXCLUDED
    assert "travel date is before observation date" in reason


def test_has_required_data_for_valid_observation():
    observation = make_valid_observation()

    assert has_required_data(observation) is True


def test_has_required_data_for_invalid_observation():
    observation = make_valid_observation()
    observation.origin = None

    assert has_required_data(observation) is False