from datetime import date, datetime
from enum import Enum
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookingWindow(str, Enum):
    T_1 = "T+1"
    T_7 = "T+7"
    T_15 = "T+15"
    T_30 = "T+30"
    T_45 = "T+45"


ROUTE_PATTERN = re.compile(r"^[A-Z]{3}-[A-Z]{3}$")


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def validate_route(value: str) -> str:
    value = value.upper()
    if not ROUTE_PATTERN.fullmatch(value) or value[:3] == value[4:]:
        raise ValueError("route must be two distinct IATA codes, e.g. DEL-BOM")
    return value


class VersionMetadata(APIModel):
    observation_set_version: str
    basket_version: str
    weight_version: str
    methodology_version: str
    calculation_version: str
    execution_checksum: str | None = None


class UnavailableResponse(APIModel):
    status: str = "unavailable"
    detail: str
