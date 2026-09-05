from datetime import date, datetime
from decimal import Decimal
from pydantic import Field, field_validator
from .common import APIModel, validate_route


class QualityMetricIn(APIModel):
    metric_date: date
    route: str | None = None
    source: str | None = None
    observation_count: int = Field(ge=0)
    route_coverage: Decimal | None = Field(default=None, ge=0, le=1)
    source_coverage: Decimal | None = Field(default=None, ge=0, le=1)
    freshness_minutes: int | None = Field(default=None, ge=0)
    missing_observations: int = Field(default=0, ge=0)
    invalid_observations: int = Field(default=0, ge=0)
    anomalous_valid_observations: int = Field(default=0, ge=0)
    status: str
    generated_at: datetime

    @field_validator("route")
    @classmethod
    def valid_route(cls, value: str | None) -> str | None:
        return validate_route(value) if value else value


class QualityMetricOut(QualityMetricIn):
    id: int
