from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
import hashlib
from typing import Any, Optional, Union


@dataclass
class RawFareRecord:
    """
    Canonical raw airfare observation collected from an external or synthetic source.

    This model represents data as received by the data-collection
    layer and conforms to the shared canonical observation contract.
    """

    origin: str
    destination: str

    travel_date: date
    observation_date: date

    booking_window: Union[int, str]

    airline: str
    flight_number: str
    departure_time: Union[time, str]

    cabin_class: str
    fare_type: str
    baggage_characteristics: str

    fare_amount: float
    currency: str = "INR"

    source: str = "mock"
    observation_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    base_fare: Optional[float] = None
    taxes: Optional[float] = None
    mandatory_charges: Optional[float] = None

    metadata: dict[str, Any] = field(default_factory=dict)
    observation_id: Optional[str] = None

    def __post_init__(self):
        # Auto-compute base fare, taxes, and fees if only fare_amount was provided
        if self.base_fare is None and self.fare_amount is not None and self.fare_amount > 0:
            self.base_fare = round(self.fare_amount * 0.82, 2)
            self.taxes = round(self.fare_amount * 0.15, 2)
            self.mandatory_charges = round(self.fare_amount - self.base_fare - self.taxes, 2)

        # Generate unique observation identifier if not set
        if not self.observation_id:
            dep_str = self.departure_time.strftime("%H:%M") if isinstance(self.departure_time, time) else str(self.departure_time)
            bw_str = f"T+{self.booking_window}" if isinstance(self.booking_window, int) else str(self.booking_window)
            ts_str = self.observation_timestamp.isoformat() if hasattr(self.observation_timestamp, "isoformat") else str(self.observation_timestamp)
            ident_str = f"{self.origin}-{self.destination}|{self.travel_date}|{self.airline}|{self.flight_number}|{dep_str}|{bw_str}|{self.source}|{ts_str}"
            self.observation_id = hashlib.sha256(ident_str.encode("utf-8")).hexdigest()

    @property
    def route(self) -> str:
        return f"{self.origin}-{self.destination}"

    @property
    def total_fare(self) -> float:
        return self.fare_amount

    @property
    def departure_date(self) -> date:
        return self.travel_date

    @property
    def collection_timestamp(self) -> datetime:
        return self.observation_timestamp


# Alias to bridge RawFareObservation terminology identically
RawFareObservation = RawFareRecord