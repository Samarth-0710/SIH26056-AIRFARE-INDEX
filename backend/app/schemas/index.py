from datetime import date, datetime
from decimal import Decimal
from pydantic import Field, field_validator
from .common import APIModel, BookingWindow, VersionMetadata


class IndexResultIn(VersionMetadata):
    observation_date: date
    booking_window: BookingWindow
    index_value: Decimal | None = Field(default=None, gt=0)
    status: str
    calculation_timestamp: datetime


class IndexResultOut(APIModel):
    index: Decimal | None
    previous_index: Decimal | None = None
    change_percent: Decimal | None = None
    timestamp: datetime
    observation_date: date
    booking_window: BookingWindow
    status: str
    methodology_version: str
    basket_version: str
    weight_version: str
    calculation_version: str
    observation_set_version: str
    execution_checksum: str | None = None


class IndexHistoryOut(APIModel):
    items: list[IndexResultOut]
