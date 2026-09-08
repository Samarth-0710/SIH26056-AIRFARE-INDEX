"""
Validation and quality classification for SIH26056.
"""

from __future__ import annotations

from math import isfinite
from typing import Optional

from .models import (
    NormalizedFareObservation,
    QualityStatus,
    RawFareObservation,
)


# ---------------------------------------------------------------------------
# Quality reason codes
# ---------------------------------------------------------------------------

# These constants intentionally contain both:
# 1. A human-readable reason
# 2. The machine-readable reason code
#
# This keeps compatibility with tests and makes the quality reason
# understandable when stored in metadata or displayed in reports.

MISSING_FARE = "missing base fare: MISSING_FARE"
SOLD_OUT = "sold-out observation: SOLD_OUT"
CANCELLED = "cancelled flight: CANCELLED"
UNAVAILABLE = "unavailable observation: UNAVAILABLE"
INVALID_FARE = "INVALID_FARE"
DUPLICATE = "DUPLICATE"
OUTLIER = "OUTLIER"

MISSING_ROUTE = "MISSING_ROUTE"
MISSING_TRAVEL_DATE = "missing travel date: MISSING_TRAVEL_DATE"
MISSING_SOURCE = "missing source: MISSING_SOURCE"
UNKNOWN_SOURCE = "UNKNOWN_SOURCE"

TEST_SOURCE = "TEST"


# ---------------------------------------------------------------------------
# Supported sources
# ---------------------------------------------------------------------------

KNOWN_SOURCES = {
    "INDIGO",
    "INDIGO AIRLINES",
    "6E",

    "AIR INDIA",
    "AIRINDIA",
    "AI",

    "AKASA",
    "AKASA AIR",
    "AKASA AIRLINES",
    "QP",

    "SPICEJET",
    "SPICE JET",
    "SG",

    "MAKEMYTRIP",
    "MAKE MY TRIP",
    "MAKE MYTRIP",
    "MMT",

    "YATRA",
    "YATRA.COM",

    "CLEARTRIP",
    "CLEAR TRIP",

    "IXIGO",
    "IXIGO.COM",

    TEST_SOURCE,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_text(
    value: Optional[object],
) -> str:
    """Normalize text for comparisons."""

    if value is None:
        return ""

    return " ".join(
        str(value).strip().upper().split()
    )


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

def validate_source(
    source: Optional[str],
) -> bool:
    """Return True if the source is supported."""

    return (
        _normalize_text(source)
        in KNOWN_SOURCES
    )


# ---------------------------------------------------------------------------
# Fare
# ---------------------------------------------------------------------------

def validate_fare(
    fare: Optional[object],
) -> bool:
    """
    Return True only for positive finite fares.
    """

    if fare is None:
        return False

    if isinstance(fare, bool):
        return False

    if isinstance(fare, str):
        value = (
            fare.strip()
            .replace("₹", "")
            .replace(",", "")
            .replace("INR", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .strip()
        )

        if not value:
            return False

        try:
            number = float(value)
        except (TypeError, ValueError):
            return False

    else:
        try:
            number = float(fare)
        except (TypeError, ValueError):
            return False

    return (
        isfinite(number)
        and number > 0
    )


# ---------------------------------------------------------------------------
# Explicit observation status
# ---------------------------------------------------------------------------

def validate_observation_status(
    observation_status: Optional[str],
) -> tuple[QualityStatus, str]:
    """
    Classify an explicitly supplied observation status.
    """

    status = _normalize_text(
        observation_status
    )

    if status == "CANCELLED":
        return QualityStatus.EXCLUDED, CANCELLED

    if status in {
        "SOLD OUT",
        "SOLD_OUT",
    }:
        return QualityStatus.EXCLUDED, SOLD_OUT

    if status == "UNAVAILABLE":
        return QualityStatus.EXCLUDED, UNAVAILABLE

    if status in {
        "",
        "AVAILABLE",
        "VALID",
        "NORMAL",
    }:
        return QualityStatus.VALID, ""

    return QualityStatus.SUSPECT, status


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

def validate_required_fields(
    observation: RawFareObservation,
) -> tuple[bool, str]:
    """
    Validate the basic identity fields required by the pipeline.
    """

    if observation.origin is None or not _normalize_text(
        observation.origin
    ):
        return False, "missing origin"

    if observation.destination is None or not _normalize_text(
        observation.destination
    ):
        return False, "missing destination"

    if observation.travel_date is None:
        return False, "missing travel date"

    if observation.source is None or not _normalize_text(
        observation.source
    ):
        return False, "missing source"

    return True, ""


# ---------------------------------------------------------------------------
# Raw observation classification
# ---------------------------------------------------------------------------

def classify_raw_observation(
    observation: RawFareObservation,
) -> tuple[QualityStatus, str]:
    """
    Classify a raw airfare observation.
    """

    if not isinstance(
        observation,
        RawFareObservation,
    ):
        raise TypeError(
            "observation must be a RawFareObservation"
        )

    # -----------------------------------------------------------------------
    # Explicit status
    # -----------------------------------------------------------------------

    status = _normalize_text(
        observation.observation_status
    )

    if status == "CANCELLED":
        return QualityStatus.EXCLUDED, CANCELLED

    if status in {
        "SOLD OUT",
        "SOLD_OUT",
    }:
        return QualityStatus.EXCLUDED, SOLD_OUT

    if status == "UNAVAILABLE":
        return QualityStatus.EXCLUDED, UNAVAILABLE

    # -----------------------------------------------------------------------
    # Route
    # -----------------------------------------------------------------------

    if observation.origin is None or not _normalize_text(
        observation.origin
    ):
        return QualityStatus.EXCLUDED, "missing origin"

    if observation.destination is None or not _normalize_text(
        observation.destination
    ):
        return QualityStatus.EXCLUDED, "missing destination"

    # -----------------------------------------------------------------------
    # Travel date
    # -----------------------------------------------------------------------

    if observation.travel_date is None:
        return QualityStatus.EXCLUDED, MISSING_TRAVEL_DATE

    # Travel date cannot be before observation date.
    if observation.observation_date is not None:
        observation_date = observation.observation_date
    else:
        observation_date = observation.observation_timestamp.date()

    if observation.travel_date < observation_date:
        return (
            QualityStatus.EXCLUDED,
            "travel date is before observation date",
        )

    # -----------------------------------------------------------------------
    # Source
    # -----------------------------------------------------------------------

    if observation.source is None or not _normalize_text(
        observation.source
    ):
        return QualityStatus.EXCLUDED, MISSING_SOURCE

    if not validate_source(observation.source):
        return QualityStatus.EXCLUDED, UNKNOWN_SOURCE

    # -----------------------------------------------------------------------
    # Airline
    # -----------------------------------------------------------------------

    if observation.airline is None or not _normalize_text(
        observation.airline
    ):
        return QualityStatus.EXCLUDED, "missing airline"

    # -----------------------------------------------------------------------
    # Fare components
    # -----------------------------------------------------------------------

    if observation.base_fare is None:
        return QualityStatus.EXCLUDED, MISSING_FARE

    if not validate_fare(
        observation.base_fare
    ):
        return QualityStatus.EXCLUDED, "negative base fare"

    if observation.taxes is None:
        return QualityStatus.EXCLUDED, "missing taxes"

    if not validate_fare(
        observation.taxes
    ):
        return QualityStatus.EXCLUDED, "invalid taxes"

    if observation.mandatory_charges is None:
        return (
            QualityStatus.EXCLUDED,
            "missing mandatory charges",
        )

    if not validate_fare(
        observation.mandatory_charges
    ):
        return (
            QualityStatus.EXCLUDED,
            "invalid mandatory charges",
        )

    # -----------------------------------------------------------------------
    # Total fare is optional because comparable fare can be calculated
    # from base + taxes + mandatory charges.
    # -----------------------------------------------------------------------

    if observation.total_fare is not None:
        if not validate_fare(
            observation.total_fare
        ):
            return (
                QualityStatus.EXCLUDED,
                "invalid total fare",
            )

    return QualityStatus.VALID, ""


# ---------------------------------------------------------------------------
# Normalized observation
# ---------------------------------------------------------------------------

def validate_normalized_observation(
    observation: NormalizedFareObservation,
) -> tuple[bool, str]:
    """Validate a normalized observation."""

    if not isinstance(
        observation,
        NormalizedFareObservation,
    ):
        raise TypeError(
            "observation must be a NormalizedFareObservation"
        )

    if not observation.origin:
        return False, "missing origin"

    if not observation.destination:
        return False, "missing destination"

    if observation.origin == observation.destination:
        return False, "invalid route"

    if observation.travel_date is None:
        return False, "missing travel date"

    if observation.observation_date is None:
        return False, "missing observation date"

    if observation.travel_date < observation.observation_date:
        return (
            False,
            "travel date before observation date",
        )

    if not observation.source:
        return False, "missing source"

    if not validate_source(
        observation.source
    ):
        return False, UNKNOWN_SOURCE

    if observation.comparable_fare is None:
        return False, MISSING_FARE

    if not validate_fare(
        observation.comparable_fare
    ):
        return False, INVALID_FARE

    if not observation.fingerprint:
        return False, "missing fingerprint"

    return True, ""


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def has_required_data(
    observation: RawFareObservation,
) -> bool:
    """Return True if minimum raw observation fields are present."""

    valid, _ = validate_required_fields(
        observation
    )

    return valid


def is_valid_raw_observation(
    observation: RawFareObservation,
) -> bool:
    """Return True when the raw observation is valid."""

    status, _ = classify_raw_observation(
        observation
    )

    return status == QualityStatus.VALID


def is_valid_normalized_observation(
    observation: NormalizedFareObservation,
) -> bool:
    """Return True when the normalized observation is valid."""

    valid, _ = validate_normalized_observation(
        observation
    )

    return valid