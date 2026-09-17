from decimal import Decimal
from pydantic import Field, field_validator
from .common import APIModel, validate_route


class RouteIndexIn(APIModel):
    route: str
    index_value: Decimal | None = Field(default=None, gt=0)
    status: str
    weight: Decimal | None = Field(default=None, ge=0, le=1)
    contribution: Decimal | None = None

    _route = field_validator("route")(validate_route)


class RouteOut(APIModel):
    route: str
    origin: str
    destination: str
    active: bool


class RouteIndexOut(APIModel):
    route: str
    index: float | None
    previous_index: float | None = None
    change_percent: float | None = None
    weight: float | None = None
    contribution: float | None = None
    timestamp: object
    booking_window: str
    status: str


class RouteContributionOut(APIModel):
    route: str
    weight: float
    route_index: float
    level_contribution: float
    point_contribution: float
    percentage_share_of_change: float
