from datetime import date, datetime
from decimal import Decimal
from pydantic import Field, field_validator
from .common import APIModel, BookingWindow


class FareObservationIn(APIModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    travel_date: date
    observation_date: date
    booking_window: BookingWindow
    airline: str = Field(min_length=1, max_length=20)
    flight_number: str = Field(min_length=1, max_length=30)
    departure_time: str = Field(min_length=1, max_length=20)
    cabin_class: str = Field(min_length=1, max_length=30)
    fare_type: str = Field(min_length=1, max_length=50)
    baggage_characteristics: str = Field(min_length=1, max_length=100)
    base_fare: Decimal | None = Field(default=None, ge=0)
    taxes: Decimal | None = Field(default=None, ge=0)
    mandatory_charges: Decimal | None = Field(default=None, ge=0)
    comparable_fare: Decimal = Field(gt=0)
    source: str = Field(min_length=1, max_length=80)
    fingerprint: str = Field(min_length=1, max_length=128)
    quality_status: str
    observation_timestamp: datetime
    metadata: dict = Field(default_factory=dict)

    @field_validator("origin", "destination", "airline", "flight_number", "cabin_class", "fare_type", "baggage_characteristics")
    @classmethod
    def uppercase(cls, value: str) -> str:
        return value.upper()
