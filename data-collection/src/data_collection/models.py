from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any


@dataclass
class RawFareRecord:
    """
    Raw airfare observation collected from an external source.

    This model represents data as received by the data-collection
    layer. Normalization and quality classification are handled
    downstream by the data-quality module.
    """

    origin: str
    destination: str

    travel_date: date
    observation_date: date

    booking_window: int

    airline: str
    flight_number: str
    departure_time: time

    cabin_class: str
    fare_type: str
    baggage_characteristics: str

    fare_amount: float
    currency: str

    source: str
    observation_timestamp: datetime

    metadata: dict[str, Any] = field(default_factory=dict)