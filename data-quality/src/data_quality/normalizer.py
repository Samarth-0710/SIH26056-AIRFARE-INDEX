"""
Fare normalization for SIH26056.

This module converts RawFareObservation objects into
NormalizedFareObservation objects.

Responsibilities:
- normalize text and route values
- normalize fare values
- calculate comparable mandatory fare
- calculate booking window
- generate fare fingerprint
- preserve fare components for auditing

This module does NOT:
- calculate airfare indices
- calculate price relatives
- apply statistical weights
- calculate the national index
- automatically remove outliers
"""

from __future__ import annotations

import math
from datetime import date
from typing import Optional

from .booking_window import calculate_booking_window
from .fingerprint import generate_fare_fingerprint
from .models import (
    NormalizedFareObservation,
    QualityStatus,
    RawFareObservation,
)


def normalize_text(value: Optional[str]) -> str:
    """
    Normalize a text field.

    Leading/trailing whitespace is removed and text is
    converted to uppercase.
    """
    if value is None:
        return ""

    return str(value).strip().upper()


def normalize_route_code(value: Optional[str]) -> str:
    """
    Normalize an airport/route code.
    """
    return normalize_text(value)


def normalize_source(value: Optional[str]) -> str:
    """
    Normalize the source name.
    """
    return normalize_text(value)


def normalize_fare_value(value: object) -> Optional[float]:
    """
    Convert a raw fare value into a float.

    Handles values such as:

        5000
        5000.50
        "5,000"
        "₹5,000"
        "INR 5,000"
        "inr 5,000"

    Returns None when the value cannot be converted.
    """

    if value is None:
        return None

    # bool is a subclass of int, so reject it explicitly.
    if isinstance(value, bool):
        return None

    # Numeric values.
    if isinstance(value, (int, float)):
        numeric_value = float(value)

        if not math.isfinite(numeric_value):
            return None

        return numeric_value

    text = str(value).strip()

    if not text:
        return None

    # Normalize currency text before removing the currency marker.
    cleaned = (
        text
        .replace("₹", "")
        .replace("INR", "")
        .replace("inr", "")
        .replace(",", "")
        .strip()
    )

    try:
        numeric_value = float(cleaned)
    except ValueError:
        return None

    if not math.isfinite(numeric_value):
        return None

    return numeric_value


def calculate_comparable_fare(
    base_fare: Optional[float],
    taxes: Optional[float],
    mandatory_charges: Optional[float],
) -> Optional[float]:
    """
    Calculate the comparable mandatory fare.

    Comparable fare:

        base fare
        + taxes
        + mandatory charges

    Optional extras such as voluntary seat selection or meals
    are not included.
    """

    if (
        base_fare is None
        or taxes is None
        or mandatory_charges is None
    ):
        return None

    if (
        base_fare < 0
        or taxes < 0
        or mandatory_charges < 0
    ):
        return None

    return base_fare + taxes + mandatory_charges


def _get_observation_date(
    observation: RawFareObservation,
) -> date:
    """
    Determine the observation date.

    Prefer the explicitly supplied observation_date.

    If it is missing, derive the date from observation_timestamp.
    """

    if observation.observation_date is not None:
        return observation.observation_date

    return observation.observation_timestamp.date()


def normalize_fare_observation(
    observation: RawFareObservation,
) -> NormalizedFareObservation:
    """
    Convert one raw airfare observation into the common
    normalized fare structure.

    The normalized structure is designed to be compatible
    with the Statistical Engine's FareObservation contract.
    """

    if observation.travel_date is None:
        raise ValueError(
            "Travel date is required for normalization."
        )

    observation_date = _get_observation_date(observation)

    # Calculate the exact lead-time booking window.
    booking_window = calculate_booking_window(
        observation_date,
        observation.travel_date,
    )

    # Normalize identifying information.
    origin = normalize_route_code(
        observation.origin
    )

    destination = normalize_route_code(
        observation.destination
    )

    airline = normalize_text(
        observation.airline
    )

    flight_number = normalize_text(
        observation.flight_number
    )

    departure_time = normalize_text(
        observation.departure_time
    )

    cabin_class = normalize_text(
        observation.cabin_class
    )

    fare_type = normalize_text(
        observation.fare_type
    )

    baggage_characteristics = normalize_text(
        observation.baggage_characteristics
    )

    source = normalize_source(
        observation.source
    )

    # Normalize fare components.
    base_fare = normalize_fare_value(
        observation.base_fare
    )

    taxes = normalize_fare_value(
        observation.taxes
    )

    mandatory_charges = normalize_fare_value(
        observation.mandatory_charges
    )

    # Construct comparable mandatory fare.
    comparable_fare = calculate_comparable_fare(
        base_fare=base_fare,
        taxes=taxes,
        mandatory_charges=mandatory_charges,
    )

    # Generate deterministic fare fingerprint.
    fingerprint = generate_fare_fingerprint(
        origin=origin,
        destination=destination,
        travel_date=observation.travel_date,
        flight_number=flight_number,
        departure_time=departure_time,
        cabin_class=cabin_class,
        fare_type=fare_type,
        baggage_characteristics=baggage_characteristics,
    )

    return NormalizedFareObservation(
        origin=origin,
        destination=destination,
        travel_date=observation.travel_date,
        observation_date=observation_date,
        booking_window=booking_window,
        airline=airline,
        flight_number=flight_number,
        departure_time=departure_time,
        cabin_class=cabin_class,
        fare_type=fare_type,
        baggage_characteristics=baggage_characteristics,
        base_fare=base_fare,
        taxes=taxes,
        mandatory_charges=mandatory_charges,
        comparable_fare=comparable_fare,
        source=source,
        observation_timestamp=observation.observation_timestamp,
        fingerprint=fingerprint,
        quality_status=QualityStatus.VALID,
        quality_reason="",
        metadata=dict(observation.metadata),
    )