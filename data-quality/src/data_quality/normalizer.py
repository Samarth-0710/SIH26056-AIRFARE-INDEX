"""
Fare normalization for SIH26056.

This module converts raw airfare observations into normalized
observations compatible with the Statistical Index Engine.
"""

from __future__ import annotations

from datetime import date, datetime
from math import isfinite
from typing import Optional

from .booking_window import calculate_booking_window
from .fingerprint import generate_fingerprint
from .models import (
    NormalizedFareObservation,
    QualityStatus,
    RawFareObservation,
)


# ---------------------------------------------------------------------------
# Supported source aliases
# ---------------------------------------------------------------------------

SOURCE_ALIASES = {
    # Airlines
    "INDIGO": "INDIGO",
    "INDIGO AIRLINES": "INDIGO",
    "6E": "INDIGO",

    "AIR INDIA": "AIR INDIA",
    "AIRINDIA": "AIR INDIA",
    "AI": "AIR INDIA",

    "AKASA": "AKASA AIR",
    "AKASA AIR": "AKASA AIR",
    "AKASA AIRLINES": "AKASA AIR",
    "QP": "AKASA AIR",

    "SPICEJET": "SPICEJET",
    "SPICE JET": "SPICEJET",
    "SG": "SPICEJET",

    # OTAs
    "MAKEMYTRIP": "MAKEMYTRIP",
    "MAKE MY TRIP": "MAKEMYTRIP",
    "MAKE MYTRIP": "MAKEMYTRIP",
    "MMT": "MAKEMYTRIP",

    "YATRA": "YATRA",
    "YATRA.COM": "YATRA",

    "CLEARTRIP": "CLEARTRIP",
    "CLEAR TRIP": "CLEARTRIP",

    "IXIGO": "IXIGO",
    "IXIGO.COM": "IXIGO",

    # Controlled test source
    "TEST": "TEST",
}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_text(value: Optional[object]) -> str:
    """Normalize text by trimming, upper-casing and collapsing whitespace."""

    if value is None:
        return ""

    return " ".join(
        str(value).strip().upper().split()
    )


def normalize_route_code(value: Optional[object]) -> str:
    """Normalize an airport code or route component."""

    return normalize_text(value)


# ---------------------------------------------------------------------------
# Source helpers
# ---------------------------------------------------------------------------

def normalize_source(value: Optional[object]) -> str:
    """
    Convert a source alias to its canonical source name.

    Unknown sources are rejected rather than silently mapped.
    """

    normalized = normalize_text(value)

    if normalized not in SOURCE_ALIASES:
        raise ValueError(
            f"unknown source: {value}"
        )

    return SOURCE_ALIASES[normalized]


def is_known_source(value: Optional[object]) -> bool:
    """Return True if the supplied source is supported."""

    if value is None:
        return False

    return normalize_text(value) in SOURCE_ALIASES


# ---------------------------------------------------------------------------
# Fare helpers
# ---------------------------------------------------------------------------

def normalize_fare_value(
    value: Optional[object],
) -> Optional[float]:
    """
    Convert a raw fare value to a finite float.

    This function performs numeric normalization only.

    Important:
    Negative values are preserved here so validation logic can identify
    them as invalid fares. They are not silently converted to None.

    Examples:
        4500       -> 4500.0
        "4,500"    -> 4500.0
        "₹4,500"   -> 4500.0
        -500       -> -500.0
        "abc"      -> None
        None       -> None
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, str):
        cleaned = value.strip()

        if not cleaned:
            return None

        cleaned = (
            cleaned
            .replace("₹", "")
            .replace(",", "")
            .replace("INR", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .strip()
        )

        if not cleaned:
            return None

        try:
            number = float(cleaned)
        except (TypeError, ValueError):
            return None

    else:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

    if not isfinite(number):
        return None

    return number


# ---------------------------------------------------------------------------
# Comparable fare
# ---------------------------------------------------------------------------

def calculate_comparable_fare(
    base_fare: Optional[object],
    taxes: Optional[object],
    mandatory_charges: Optional[object],
    total_fare: Optional[object] = None,
) -> Optional[float]:
    """
    Calculate the comparable fare.

    The preferred calculation is:

        base fare + taxes + mandatory charges

    All three components must be present and positive.

    If a component is missing or invalid, None is returned.

    A supplied total fare is used only as a fallback when all required
    fare components are unavailable.
    """

    base = normalize_fare_value(base_fare)
    tax = normalize_fare_value(taxes)
    mandatory = normalize_fare_value(mandatory_charges)

    # The documented comparable fare requires all three mandatory
    # components to be available and positive.
    if (
        base is not None
        and tax is not None
        and mandatory is not None
        and base > 0
        and tax > 0
        and mandatory > 0
    ):
        return base + tax + mandatory

    # If a complete component breakdown is unavailable, use a valid
    # total fare as fallback.
    total = normalize_fare_value(total_fare)

    if total is not None and total > 0:
        return total

    return None


# ---------------------------------------------------------------------------
# Observation date
# ---------------------------------------------------------------------------

def _get_observation_date(
    observation: RawFareObservation,
) -> date:
    """Get the observation date from the explicit date or timestamp."""

    if observation.observation_date is not None:
        if isinstance(
            observation.observation_date,
            datetime,
        ):
            return observation.observation_date.date()

        return observation.observation_date

    if isinstance(
        observation.observation_timestamp,
        datetime,
    ):
        return observation.observation_timestamp.date()

    raise ValueError(
        "Observation date is required"
    )


# ---------------------------------------------------------------------------
# Main normalization
# ---------------------------------------------------------------------------

def normalize_fare_observation(
    observation: RawFareObservation,
) -> NormalizedFareObservation:
    """
    Normalize one raw airfare observation.
    """

    if not isinstance(
        observation,
        RawFareObservation,
    ):
        raise TypeError(
            "observation must be a RawFareObservation"
        )

    # Travel date is mandatory.
    if observation.travel_date is None:
        raise ValueError(
            "Travel date is required"
        )

    travel_date = observation.travel_date
    observation_date = _get_observation_date(observation)

    # -----------------------------------------------------------------------
    # Route
    # -----------------------------------------------------------------------

    origin = normalize_route_code(
        observation.origin
    )

    destination = normalize_route_code(
        observation.destination
    )

    if not origin:
        raise ValueError(
            "Origin is required"
        )

    if not destination:
        raise ValueError(
            "Destination is required"
        )

    if origin == destination:
        raise ValueError(
            "Origin and destination cannot be the same"
        )

    # -----------------------------------------------------------------------
    # Source
    # -----------------------------------------------------------------------

    source = normalize_source(
        observation.source
    )

    # -----------------------------------------------------------------------
    # Text fields
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Fare components
    # -----------------------------------------------------------------------

    base_fare = normalize_fare_value(
        observation.base_fare
    )

    taxes = normalize_fare_value(
        observation.taxes
    )

    mandatory_charges = normalize_fare_value(
        observation.mandatory_charges
    )

    comparable_fare = calculate_comparable_fare(
        base_fare=observation.base_fare,
        taxes=observation.taxes,
        mandatory_charges=observation.mandatory_charges,
        total_fare=observation.total_fare,
    )

    # -----------------------------------------------------------------------
    # Booking window
    # -----------------------------------------------------------------------

    lead_days = (
        travel_date - observation_date
    ).days

    booking_window = calculate_booking_window(
        observation_date,
        travel_date,
    )

    # -----------------------------------------------------------------------
    # Fingerprint
    # -----------------------------------------------------------------------

    fingerprint = generate_fingerprint(
        origin=origin,
        destination=destination,
        travel_date=travel_date,
        flight_number=flight_number,
        departure_time=departure_time,
        cabin_class=cabin_class,
        fare_type=fare_type,
        baggage_characteristics=baggage_characteristics,
    )

    # -----------------------------------------------------------------------
    # Quality status
    # -----------------------------------------------------------------------

    quality_status = QualityStatus.VALID
    quality_reason = ""

    raw_status = normalize_text(
        observation.observation_status
    )

    if raw_status in {
        "CANCELLED",
        "SOLD OUT",
        "SOLD_OUT",
        "UNAVAILABLE",
    }:
        quality_status = QualityStatus.EXCLUDED
        quality_reason = raw_status

    elif comparable_fare is None:
        quality_status = QualityStatus.EXCLUDED
        quality_reason = "MISSING_FARE"

    # -----------------------------------------------------------------------
    # Metadata
    # -----------------------------------------------------------------------

    metadata = dict(
        observation.metadata
    )

    metadata.update(
        {
            "canonical_source": source,
            "lead_days": lead_days,
            "quality_reason_code": quality_reason,
            "observation_status": raw_status,
        }
    )

    # -----------------------------------------------------------------------
    # Result
    # -----------------------------------------------------------------------

    return NormalizedFareObservation(
        origin=origin,
        destination=destination,
        travel_date=travel_date,
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
        quality_status=quality_status,
        quality_reason=quality_reason,
        metadata=metadata,
    )


def normalize_observation(
    observation: RawFareObservation,
) -> NormalizedFareObservation:
    """Backward-compatible alias."""

    return normalize_fare_observation(
        observation
    )