"""
Data-quality validation for SIH26056.

This module checks raw and normalized fare observations for:
- missing required fields
- invalid fare values
- invalid dates
- cancelled flights
- sold-out observations
- missing fare components
- missing fields required by the Statistical Engine

It does NOT:
- calculate the airfare index
- calculate price relatives
- apply route weights
- delete observations
- automatically reject unusual fares

Booking windows are derived from observation date and travel date
by booking_window.py. A booking_window supplied by the collection
layer is treated as optional input information and is not required
for validation.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Optional

from .models import (
    NormalizedFareObservation,
    QualityStatus,
    RawFareObservation,
)


def _is_missing(value: object) -> bool:
    """Return True when a value is None or an empty string."""
    return value is None or (
        isinstance(value, str) and not value.strip()
    )


def _get_observation_date(
    observation: RawFareObservation,
) -> date:
    """
    Determine the observation date.

    Prefer the explicitly supplied observation_date.
    Otherwise derive it from observation_timestamp.
    """
    if observation.observation_date is not None:
        return observation.observation_date

    return observation.observation_timestamp.date()


def validate_route(
    observation: RawFareObservation,
) -> Optional[str]:
    """Check whether origin and destination are present."""

    if _is_missing(observation.origin):
        return "missing origin"

    if _is_missing(observation.destination):
        return "missing destination"

    if (
        isinstance(observation.origin, str)
        and isinstance(observation.destination, str)
        and observation.origin.strip().upper()
        == observation.destination.strip().upper()
    ):
        return "origin and destination are identical"

    return None


def validate_travel_date(
    observation: RawFareObservation,
) -> Optional[str]:
    """Check whether the travel date is present and valid."""

    if observation.travel_date is None:
        return "missing travel date"

    if not isinstance(observation.travel_date, date):
        return "invalid travel date"

    observation_date = _get_observation_date(observation)

    if observation.travel_date < observation_date:
        return "travel date is before observation date"

    return None


def validate_airline(
    observation: RawFareObservation,
) -> Optional[str]:
    """Check whether airline information is present."""

    if _is_missing(observation.airline):
        return "missing airline"

    return None


def validate_flight_details(
    observation: RawFareObservation,
) -> list[str]:
    """
    Validate fields required for fare comparability.

    These fields are used by the normalized observation and
    fare fingerprint consumed by the Statistical Engine.
    """

    fields = {
        "flight number": observation.flight_number,
        "departure time": observation.departure_time,
        "cabin class": observation.cabin_class,
        "fare type": observation.fare_type,
        "baggage characteristics": observation.baggage_characteristics,
        "source": observation.source,
    }

    reasons: list[str] = []

    for name, value in fields.items():
        if _is_missing(value):
            reasons.append(f"missing {name}")

    return reasons


def validate_fare_components(
    observation: RawFareObservation,
) -> list[str]:
    """
    Validate the mandatory fare components.

    Base fare, taxes and mandatory charges are required for
    construction of the comparable mandatory fare.
    """

    components = {
        "base fare": observation.base_fare,
        "taxes": observation.taxes,
        "mandatory charges": observation.mandatory_charges,
    }

    reasons: list[str] = []

    for name, value in components.items():
        if value is None:
            reasons.append(f"missing {name}")
            continue

        if isinstance(value, bool):
            reasons.append(f"invalid {name}")
            continue

        if not isinstance(value, (int, float)):
            reasons.append(f"invalid {name}")
            continue

        if not math.isfinite(float(value)):
            reasons.append(f"invalid {name}")
            continue

        if value < 0:
            reasons.append(f"negative {name}")

    return reasons


def validate_comparable_fare(
    observation: RawFareObservation,
) -> Optional[str]:
    """Validate the raw total fare when supplied."""

    if observation.total_fare is None:
        return None

    if isinstance(observation.total_fare, bool):
        return "invalid total fare"

    if not isinstance(observation.total_fare, (int, float)):
        return "invalid total fare"

    if not math.isfinite(float(observation.total_fare)):
        return "invalid total fare"

    if observation.total_fare < 0:
        return "negative total fare"

    return None


def validate_booking_window(
    observation: RawFareObservation,
) -> Optional[str]:
    """
    Validate the supplied booking-window value when present.

    The collection layer may provide this field, but it is not
    required because the data-quality module derives the booking
    window from observation date and travel date.
    """

    if _is_missing(observation.booking_window):
        return None

    allowed_windows = {
        "T+1",
        "T+7",
        "T+15",
        "T+30",
        "T+45",
    }

    normalized_window = (
        str(observation.booking_window)
        .strip()
        .upper()
    )

    if normalized_window not in allowed_windows:
        return "invalid booking window"

    return None


def validate_observation_status(
    observation: RawFareObservation,
) -> Optional[str]:
    """
    Detect explicitly unavailable observations.

    Cancelled and sold-out observations are retained and classified
    as excluded rather than silently deleted.
    """

    if observation.observation_status is None:
        return None

    status = str(
        observation.observation_status
    ).strip().upper()

    if "CANCEL" in status:
        return "cancelled flight"

    if "SOLD" in status and "OUT" in status:
        return "sold-out observation"

    return None


def validate_required_fields(
    observation: RawFareObservation,
) -> list[str]:
    """
    Run the required-field and validity checks.

    Returns all detected reasons instead of stopping at the
    first problem.
    """

    reasons: list[str] = []

    route_reason = validate_route(observation)
    if route_reason is not None:
        reasons.append(route_reason)

    travel_date_reason = validate_travel_date(observation)
    if travel_date_reason is not None:
        reasons.append(travel_date_reason)

    airline_reason = validate_airline(observation)
    if airline_reason is not None:
        reasons.append(airline_reason)

    reasons.extend(
        validate_flight_details(observation)
    )

    reasons.extend(
        validate_fare_components(observation)
    )

    comparable_fare_reason = validate_comparable_fare(
        observation
    )
    if comparable_fare_reason is not None:
        reasons.append(comparable_fare_reason)

    booking_window_reason = validate_booking_window(
        observation
    )
    if booking_window_reason is not None:
        reasons.append(booking_window_reason)

    status_reason = validate_observation_status(
        observation
    )
    if status_reason is not None:
        reasons.append(status_reason)

    return reasons


def classify_raw_observation(
    observation: RawFareObservation,
) -> tuple[QualityStatus, str]:
    """
    Assign a quality status to a raw observation.

    Classification rules:

    EXCLUDED:
        cancelled, sold-out, missing, or structurally invalid
        observations.

    SUSPECT:
        unusual but potentially usable observations are handled
        by the outlier/anomaly module, not here.

    VALID:
        observation passes the basic structural checks.

    The function preserves all detected reasons.
    """

    status_reason = validate_observation_status(
        observation
    )

    if status_reason is not None:
        return QualityStatus.EXCLUDED, status_reason

    reasons = validate_required_fields(
        observation
    )

    if reasons:
        return QualityStatus.EXCLUDED, "; ".join(reasons)

    return QualityStatus.VALID, ""


def validate_normalized_observation(
    observation: NormalizedFareObservation,
) -> tuple[QualityStatus, str]:
    """
    Validate an already normalized observation.

    This is useful immediately before handing data to the
    Statistical Index Engine.
    """

    reasons: list[str] = []

    if not observation.origin:
        reasons.append("missing origin")

    if not observation.destination:
        reasons.append("missing destination")

    if (
        observation.origin
        and observation.destination
        and observation.origin == observation.destination
    ):
        reasons.append(
            "origin and destination are identical"
        )

    if not observation.airline:
        reasons.append("missing airline")

    if not observation.flight_number:
        reasons.append("missing flight number")

    if not observation.departure_time:
        reasons.append("missing departure time")

    if not observation.cabin_class:
        reasons.append("missing cabin class")

    if not observation.fare_type:
        reasons.append("missing fare type")

    if not observation.baggage_characteristics:
        reasons.append(
            "missing baggage characteristics"
        )

    if not observation.source:
        reasons.append("missing source")

    if observation.travel_date is None:
        reasons.append("missing travel date")

    if observation.travel_date < observation.observation_date:
        reasons.append(
            "travel date is before observation date"
        )

    if observation.base_fare is None:
        reasons.append("missing base fare")
    elif observation.base_fare < 0:
        reasons.append("negative base fare")

    if observation.taxes is None:
        reasons.append("missing taxes")
    elif observation.taxes < 0:
        reasons.append("negative taxes")

    if observation.mandatory_charges is None:
        reasons.append("missing mandatory charges")
    elif observation.mandatory_charges < 0:
        reasons.append("negative mandatory charges")

    if observation.comparable_fare is None:
        reasons.append("missing comparable fare")
    elif observation.comparable_fare < 0:
        reasons.append("negative comparable fare")

    if not observation.fingerprint:
        reasons.append("missing fare fingerprint")

    if reasons:
        return QualityStatus.EXCLUDED, "; ".join(reasons)

    return QualityStatus.VALID, ""


def has_required_data(
    observation: RawFareObservation,
) -> bool:
    """Return True if the observation passes basic validation."""

    status, _ = classify_raw_observation(
        observation
    )

    return status == QualityStatus.VALID