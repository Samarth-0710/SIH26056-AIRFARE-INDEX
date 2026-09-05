"""
Deterministic fare fingerprinting for SIH26056.

The fingerprint identifies a comparable airfare observation using
the characteristics that define the flight/fare combination.

Source is intentionally not included in the fingerprint.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Optional


def _normalize(value: Optional[object]) -> str:
    """
    Convert a fingerprint field into a deterministic string.
    """

    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    return " ".join(
        str(value).strip().upper().split()
    )


def generate_fare_fingerprint(
    origin: str,
    destination: str,
    travel_date: date,
    flight_number: str,
    departure_time: str,
    cabin_class: str,
    fare_type: str,
    baggage_characteristics: str,
) -> str:
    """
    Generate a deterministic SHA-256 fare fingerprint.

    The fingerprint is based on:

    - Origin
    - Destination
    - Travel date
    - Flight number
    - Departure time
    - Cabin class
    - Fare type
    - Baggage characteristics

    Source is deliberately excluded because source identifies
    where the observation was collected, not the comparable
    flight/fare itself.
    """

    fields = [
        _normalize(origin),
        _normalize(destination),
        _normalize(travel_date),
        _normalize(flight_number),
        _normalize(departure_time),
        _normalize(cabin_class),
        _normalize(fare_type),
        _normalize(baggage_characteristics),
    ]

    canonical_string = "|".join(fields)

    return hashlib.sha256(
        canonical_string.encode("utf-8")
    ).hexdigest()


def generate_fingerprint(
    origin: str,
    destination: str,
    travel_date: date,
    flight_number: str,
    departure_time: str,
    cabin_class: str,
    fare_type: str,
    baggage_characteristics: str,
) -> str:
    """
    Alias for generate_fare_fingerprint().

    Kept for compatibility with the normalizer.
    """

    return generate_fare_fingerprint(
        origin=origin,
        destination=destination,
        travel_date=travel_date,
        flight_number=flight_number,
        departure_time=departure_time,
        cabin_class=cabin_class,
        fare_type=fare_type,
        baggage_characteristics=baggage_characteristics,
    )


def create_fingerprint(
    origin: str,
    destination: str,
    travel_date: date,
    flight_number: str,
    departure_time: str,
    cabin_class: str,
    fare_type: str,
    baggage_characteristics: str,
) -> str:
    """
    Backward-compatible alias for fingerprint generation.
    """

    return generate_fare_fingerprint(
        origin=origin,
        destination=destination,
        travel_date=travel_date,
        flight_number=flight_number,
        departure_time=departure_time,
        cabin_class=cabin_class,
        fare_type=fare_type,
        baggage_characteristics=baggage_characteristics,
    )