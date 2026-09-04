"""
Tests for fare fingerprinting.
"""

from datetime import date

from data_quality.fingerprint import generate_fare_fingerprint


def make_fingerprint(**overrides):
    values = {
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": date(2026, 10, 1),
        "flight_number": "6E123",
        "departure_time": "10:30",
        "cabin_class": "ECONOMY",
        "fare_type": "REGULAR",
        "baggage_characteristics": "15KG",
    }

    values.update(overrides)

    return generate_fare_fingerprint(**values)


def test_same_fare_produces_same_fingerprint():
    first = make_fingerprint()
    second = make_fingerprint()

    assert first == second


def test_fingerprint_is_sha256_length():
    fingerprint = make_fingerprint()

    assert len(fingerprint) == 64


def test_different_route_changes_fingerprint():
    first = make_fingerprint(destination="BOM")
    second = make_fingerprint(destination="BLR")

    assert first != second


def test_different_travel_date_changes_fingerprint():
    first = make_fingerprint(
        travel_date=date(2026, 10, 1)
    )

    second = make_fingerprint(
        travel_date=date(2026, 10, 2)
    )

    assert first != second


def test_different_flight_changes_fingerprint():
    first = make_fingerprint(flight_number="6E123")
    second = make_fingerprint(flight_number="AI456")

    assert first != second


def test_text_whitespace_does_not_change_fingerprint():
    first = make_fingerprint(
        origin="DEL",
        destination="BOM",
    )

    second = make_fingerprint(
        origin=" DEL ",
        destination=" bom ",
    )

    assert first == second


def test_baggage_characteristics_change_fingerprint():
    first = make_fingerprint(
        baggage_characteristics="15KG"
    )

    second = make_fingerprint(
        baggage_characteristics="20KG"
    )

    assert first != second