"""
Tests for fare normalization.
"""

from datetime import date, datetime

from data_quality.models import RawFareObservation, QualityStatus
from data_quality.normalizer import (
    calculate_comparable_fare,
    normalize_fare_observation,
    normalize_fare_value,
    normalize_route_code,
    normalize_source,
    normalize_text,
)


def create_raw_observation(**overrides):
    """
    Create a realistic raw airfare observation for testing.
    """

    values = {
        "observation_timestamp": datetime(2026, 9, 1, 10, 30),
        "origin": " del ",
        "destination": " bom ",
        "travel_date": date(2026, 9, 8),
        "observation_date": date(2026, 9, 1),
        "booking_window": "T+7",
        "airline": " IndiGo ",
        "flight_number": " 6E123 ",
        "departure_time": "10:30",
        "cabin_class": " economy ",
        "fare_type": " regular ",
        "baggage_characteristics": "15KG",
        "base_fare": 4200,
        "taxes": 650,
        "mandatory_charges": 150,
        "total_fare": 5000,
        "source": " makemytrip ",
        "observation_status": "AVAILABLE",
        "metadata": {},
    }

    values.update(overrides)

    return RawFareObservation(**values)


def test_normalize_text():
    assert normalize_text("  economy ") == "ECONOMY"


def test_normalize_text_missing_value():
    assert normalize_text(None) == ""


def test_normalize_route_code():
    assert normalize_route_code(" del ") == "DEL"


def test_normalize_source():
    assert normalize_source(" MakeMyTrip ") == "MAKEMYTRIP"


def test_normalize_integer_fare():
    assert normalize_fare_value(5000) == 5000.0


def test_normalize_decimal_fare():
    assert normalize_fare_value(5000.50) == 5000.50


def test_normalize_currency_fare():
    assert normalize_fare_value("₹5,000") == 5000.0


def test_normalize_inr_fare():
    assert normalize_fare_value("INR 5,000") == 5000.0


def test_invalid_fare_returns_none():
    assert normalize_fare_value("not-a-fare") is None


def test_missing_fare_returns_none():
    assert normalize_fare_value(None) is None


def test_negative_fare_is_rejected():
    assert normalize_fare_value(-500) == -500.0


def test_comparable_fare_calculation():
    result = calculate_comparable_fare(
        base_fare=4200,
        taxes=650,
        mandatory_charges=150,
    )

    assert result == 5000


def test_missing_component_returns_none():
    result = calculate_comparable_fare(
        base_fare=4200,
        taxes=None,
        mandatory_charges=150,
    )

    assert result is None


def test_negative_component_returns_none():
    result = calculate_comparable_fare(
        base_fare=-4200,
        taxes=650,
        mandatory_charges=150,
    )

    assert result is None


def test_full_fare_normalization():
    raw = create_raw_observation()

    normalized = normalize_fare_observation(raw)

    assert normalized.origin == "DEL"
    assert normalized.destination == "BOM"

    assert normalized.travel_date == date(2026, 9, 8)
    assert normalized.observation_date == date(2026, 9, 1)

    assert normalized.booking_window.value == "T+7"

    assert normalized.airline == "INDIGO"
    assert normalized.flight_number == "6E123"

    assert normalized.cabin_class == "ECONOMY"
    assert normalized.fare_type == "REGULAR"

    assert normalized.base_fare == 4200.0
    assert normalized.taxes == 650.0
    assert normalized.mandatory_charges == 150.0

    assert normalized.comparable_fare == 5000.0

    assert normalized.source == "MAKEMYTRIP"

    assert normalized.fingerprint
    assert len(normalized.fingerprint) == 64

    assert normalized.quality_status == QualityStatus.VALID


def test_route_property():
    raw = create_raw_observation()

    normalized = normalize_fare_observation(raw)

    assert normalized.route == "DEL-BOM"


def test_lead_days_property():
    raw = create_raw_observation()

    normalized = normalize_fare_observation(raw)

    assert normalized.lead_days == 7


def test_missing_travel_date_raises_error():
    raw = create_raw_observation(
        travel_date=None
    )

    try:
        normalize_fare_observation(raw)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "Travel date is required" in str(error)


def test_unsupported_booking_window_raises_error():
    raw = create_raw_observation(
        travel_date=date(2026, 9, 7)
    )

    try:
        normalize_fare_observation(raw)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_fare_components_are_preserved():
    raw = create_raw_observation()

    normalized = normalize_fare_observation(raw)

    assert normalized.base_fare == 4200
    assert normalized.taxes == 650
    assert normalized.mandatory_charges == 150
    assert normalized.comparable_fare == 5000