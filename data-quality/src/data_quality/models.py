"""
Data models for the SIH26056 Data Quality and Fare Normalization module.

This module defines:
- RawFareObservation: input received from data collection
- NormalizedFareObservation: cleaned and standardized fare
- QualityStatus: quality classification used by the processing layer

The final normalized observation is designed to be compatible with
the Statistical Engine's FareObservation contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional


class QualityStatus(str, Enum):
    """
    Quality status assigned by the data-quality module.

    These statuses are mapped to the Statistical Engine's existing
    quality-status contract.
    """

    VALID = "VALID"
    SUSPECT = "SUSPECT"
    EXCLUDED = "EXCLUDED"
    OUTLIER = "OUTLIER"


class BookingWindow(str, Enum):
    """Supported SIH26056 booking windows."""

    T_1 = "T+1"
    T_7 = "T+7"
    T_15 = "T+15"
    T_30 = "T+30"
    T_45 = "T+45"

    @classmethod
    def from_lead_days(cls, lead_days: int) -> "BookingWindow":
        """
        Convert an exact lead-time value into a documented
        booking window.

        Only the project's five documented windows are accepted.
        """
        mapping = {
            1: cls.T_1,
            7: cls.T_7,
            15: cls.T_15,
            30: cls.T_30,
            45: cls.T_45,
        }

        if lead_days not in mapping:
            raise ValueError(
                f"Lead time {lead_days} days does not match "
                f"supported booking windows: {list(mapping.keys())}"
            )

        return mapping[lead_days]


@dataclass
class RawFareObservation:
    """
    Raw fare observation received from the data-collection layer.

    This model intentionally keeps the raw fare components separate
    so that normalization remains auditable.
    """

    observation_timestamp: datetime

    origin: Optional[str]
    destination: Optional[str]

    travel_date: Optional[date]
    observation_date: Optional[date] = None

    booking_window: Optional[str] = None

    airline: Optional[str] = None
    flight_number: Optional[str] = None
    departure_time: Optional[str] = None

    cabin_class: Optional[str] = None
    fare_type: Optional[str] = None
    baggage_characteristics: Optional[str] = None

    base_fare: Optional[float] = None
    taxes: Optional[float] = None
    mandatory_charges: Optional[float] = None
    total_fare: Optional[float] = None

    source: Optional[str] = None

    observation_status: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedFareObservation:
    """
    Cleaned and standardized fare observation.

    This is the output of the data-quality module and is intended
    to provide the fields required by the Statistical Engine.
    """

    origin: str
    destination: str

    travel_date: date
    observation_date: date

    booking_window: BookingWindow

    airline: str
    flight_number: str
    departure_time: str

    cabin_class: str
    fare_type: str
    baggage_characteristics: str

    base_fare: Optional[float]
    taxes: Optional[float]
    mandatory_charges: Optional[float]

    comparable_fare: Optional[float]

    source: str

    observation_timestamp: datetime

    fingerprint: str

    quality_status: QualityStatus

    quality_reason: str = ""

    processing_timestamp: datetime = field(
        default_factory=datetime.utcnow
    )

    processing_version: str = "1.0.0"

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def route(self) -> str:
        """Return standardized route representation."""
        return f"{self.origin}-{self.destination}"

    @property
    def lead_days(self) -> int:
        """Return the exact number of days between observation and travel."""
        return (self.travel_date - self.observation_date).days