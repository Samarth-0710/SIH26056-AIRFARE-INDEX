from decimal import Decimal
from pydantic import Field, field_validator
from .common import APIModel, validate_route


class SimulationRequest(APIModel):
    """A projection must be supplied by an approved simulation component; API does not invent one."""
    route: str
    shock_percent: Decimal = Field(ge=-100, le=1000)
    projected_index: Decimal | None = Field(default=None, gt=0)
    input_metadata: dict = Field(default_factory=dict)
    _route = field_validator("route")(validate_route)


class SimulationResponse(APIModel):
    current_index: Decimal | None
    route: str
    shock_percent: Decimal
    projected_index: Decimal | None
    impact_points: Decimal | None
    simulation: bool = True
    status: str
