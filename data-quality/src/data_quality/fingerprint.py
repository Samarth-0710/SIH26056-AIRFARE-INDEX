"""
Deterministic fare fingerprinting for SIH26056.

A fingerprint identifies the characteristics of a fare observation
that are relevant for determining whether two observations represent
the same fare configuration.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Optional


def _normalize_component(value: Optional[object]) -> str:
    """
    Convert a fingerprint component into a deterministic string.
    """
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    return str(value).strip().upper()


def generate_fare_fingerprint(
    *,
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
    Generate a deterministic SHA-256 fingerprint.

    Fingerprint components:

        origin
        destination
        travel date
        flight
        departure time
        cabin
        fare type
        baggage/fare characteristics

    The same normalized inputs always produce the same fingerprint.
    """

    components = [
        _normalize_component(origin),
        _normalize_component(destination),
        _normalize_component(travel_date),
        _normalize_component(flight_number),
        _normalize_component(departure_time),
        _normalize_component(cabin_class),
        _normalize_component(fare_type),
        _normalize_component(baggage_characteristics),
    ]

    canonical_string = "|".join(components)

    return hashlib.sha256(
        canonical_string.encode("utf-8")
    ).hexdigest()