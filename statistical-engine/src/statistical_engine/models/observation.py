"""Fare observation data models and validation for the statistical index engine.

Clean, strongly typed internal models representing comparable fare observations
for the SIH26056 Airfare Price Index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
import math
from typing import Any, Dict, Optional, Tuple, Union


class BookingWindow(str, Enum):
    """Documented booking windows for the Airfare Price Index.
    
    The methodology requires strictly separate indices for:
    - T+1:  1-day advance purchase (last minute)
    - T+7:  7-day advance purchase
    - T+15: 15-day advance purchase
    - T+30: 30-day advance purchase
    - T+45: 45-day advance purchase
    """
    T_1 = "T+1"
    T_7 = "T+7"
    T_15 = "T+15"
    T_30 = "T+30"
    T_45 = "T+45"

    @classmethod
    def from_string(cls, value: str) -> BookingWindow:
        """Parse string representation into BookingWindow enum."""
        cleaned = value.strip().upper().replace(" ", "")
        for member in cls:
            if member.value == cleaned or member.name == cleaned:
                return member
        raise ValueError(
            f"Unsupported booking window: '{value}'. "
            f"Supported windows are: {[w.value for w in cls]}"
        )

    @classmethod
    def from_lead_days(cls, days: int) -> BookingWindow:
        """Map lead days (travel_date - observation_date) to nearest documented booking window.
        
        Strict exact matching to documented windows: 1 -> T+1, 7 -> T+7, 15 -> T+15, 30 -> T+30, 45 -> T+45.
        """
        mapping = {1: cls.T_1, 7: cls.T_7, 15: cls.T_15, 30: cls.T_30, 45: cls.T_45}
        if days in mapping:
            return mapping[days]
        raise ValueError(
            f"Lead time {days} days does not match documented booking windows: {list(mapping.keys())}"
        )


class QualityStatus(str, Enum):
    """Quality and validation status of the fare observation."""
    VALID = "VALID"
    SUSPECT = "SUSPECT"
    EXCLUDED = "EXCLUDED"
    OUTLIER = "OUTLIER"


@dataclass(frozen=True)
class FareObservation:
    """Represents a clean, comparable fare observation.
    
    Adheres to the documented fare dimensions:
    - origin: 3-letter IATA airport code (e.g. 'DEL')
    - destination: 3-letter IATA airport code (e.g. 'BOM')
    - travel_date: Date of departure
    - observation_date: Date observation was recorded
    - booking_window: Documented booking window (T+1, T+7, T+15, T+30, T+45)
    - airline: Airline IATA/ICAO code or name (e.g. '6E', 'AI')
    - flight_number: Flight identifier (e.g. '6E-201')
    - departure_time: Scheduled departure time or departure time slot
    - cabin_class: Cabin class (e.g. 'ECONOMY')
    - fare_type: Fare class/brand (e.g. 'SAVER', 'FLEXI')
    - baggage_characteristics: Standardized baggage allowance (e.g. '15KG')
    - comparable_fare: Total payable comparable fare in INR (positive float)
    - source: Data source identifier (e.g. 'PORTAL_A')
    - observation_timestamp: Exact UTC/IST observation timestamp
    - quality_status: Quality status from upstream data quality module
    - metadata: Optional extension dictionary for integration
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
    comparable_fare: float
    source: str
    observation_timestamp: datetime
    quality_status: QualityStatus = QualityStatus.VALID
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate observation fields."""
        # Origin & Destination validation
        if not self.origin or not self.origin.strip():
            raise ValueError("Origin cannot be empty")
        if not self.destination or not self.destination.strip():
            raise ValueError("Destination cannot be empty")
        orig = self.origin.strip().upper()
        dest = self.destination.strip().upper()
        if orig == dest:
            raise ValueError(f"Origin and destination cannot be identical: {orig}")

        # Normalization using object.__setattr__ due to frozen dataclass
        object.__setattr__(self, "origin", orig)
        object.__setattr__(self, "destination", dest)
        object.__setattr__(self, "airline", self.airline.strip().upper())
        object.__setattr__(self, "flight_number", self.flight_number.strip().upper())
        object.__setattr__(self, "cabin_class", self.cabin_class.strip().upper())
        object.__setattr__(self, "fare_type", self.fare_type.strip().upper())
        object.__setattr__(self, "baggage_characteristics", self.baggage_characteristics.strip().upper())

        # Booking Window type check
        if isinstance(self.booking_window, str):
            object.__setattr__(self, "booking_window", BookingWindow.from_string(self.booking_window))
        elif not isinstance(self.booking_window, BookingWindow):
            raise ValueError(f"Invalid booking window type: {type(self.booking_window)}")

        # Fare numerical validation
        if not isinstance(self.comparable_fare, (int, float)):
            raise ValueError(f"Comparable fare must be a number, got {type(self.comparable_fare)}")
        fare_val = float(self.comparable_fare)
        if math.isnan(fare_val) or math.isinf(fare_val):
            raise ValueError("Comparable fare cannot be NaN or Infinite")
        if fare_val <= 0.0:
            raise ValueError(f"Comparable fare must be strictly positive (> 0), got {fare_val}")
        object.__setattr__(self, "comparable_fare", fare_val)

        # Dates validation
        if not isinstance(self.travel_date, date):
            raise ValueError(f"travel_date must be a date object, got {type(self.travel_date)}")
        if not isinstance(self.observation_date, date):
            raise ValueError(f"observation_date must be a date object, got {type(self.observation_date)}")
        if self.travel_date < self.observation_date:
            raise ValueError(
                f"Travel date ({self.travel_date}) cannot be before observation date ({self.observation_date})"
            )

        # Quality status
        if isinstance(self.quality_status, str):
            object.__setattr__(self, "quality_status", QualityStatus(self.quality_status.upper()))

    @property
    def route(self) -> str:
        """Route representation: ORIGIN-DESTINATION (e.g. 'DEL-BOM')."""
        return f"{self.origin}-{self.destination}"

    @property
    def lead_days(self) -> int:
        """Days between observation date and travel date."""
        return (self.travel_date - self.observation_date).days

    def to_dict(self) -> Dict[str, Any]:
        """Convert observation to dictionary for serialization."""
        return {
            "origin": self.origin,
            "destination": self.destination,
            "route": self.route,
            "travel_date": self.travel_date.isoformat(),
            "observation_date": self.observation_date.isoformat(),
            "booking_window": self.booking_window.value,
            "airline": self.airline,
            "flight_number": self.flight_number,
            "departure_time": self.departure_time,
            "cabin_class": self.cabin_class,
            "fare_type": self.fare_type,
            "baggage_characteristics": self.baggage_characteristics,
            "comparable_fare": self.comparable_fare,
            "source": self.source,
            "observation_timestamp": self.observation_timestamp.isoformat(),
            "quality_status": self.quality_status.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FareObservation:
        """Create FareObservation from dictionary."""
        tr_date = (
            date.fromisoformat(data["travel_date"])
            if isinstance(data["travel_date"], str)
            else data["travel_date"]
        )
        obs_date = (
            date.fromisoformat(data["observation_date"])
            if isinstance(data["observation_date"], str)
            else data["observation_date"]
        )
        obs_ts = (
            datetime.fromisoformat(data["observation_timestamp"])
            if isinstance(data["observation_timestamp"], str)
            else data["observation_timestamp"]
        )
        bw = (
            BookingWindow.from_string(data["booking_window"])
            if isinstance(data["booking_window"], str)
            else data["booking_window"]
        )
        qs = (
            QualityStatus(data.get("quality_status", "VALID"))
            if isinstance(data.get("quality_status", "VALID"), str)
            else data.get("quality_status", QualityStatus.VALID)
        )

        return cls(
            origin=data["origin"],
            destination=data["destination"],
            travel_date=tr_date,
            observation_date=obs_date,
            booking_window=bw,
            airline=data["airline"],
            flight_number=data["flight_number"],
            departure_time=str(data["departure_time"]),
            cabin_class=data["cabin_class"],
            fare_type=data["fare_type"],
            baggage_characteristics=data["baggage_characteristics"],
            comparable_fare=float(data["comparable_fare"]),
            source=data.get("source", "UNKNOWN"),
            observation_timestamp=obs_ts,
            quality_status=qs,
            metadata=data.get("metadata", {}),
        )
