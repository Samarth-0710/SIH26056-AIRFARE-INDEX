from datetime import datetime
from decimal import Decimal
from pydantic import Field
from .common import APIModel


class IntelligenceEventIn(APIModel):
    route: str | None = None
    event_type: str
    anomaly_score: Decimal | None = Field(default=None, ge=0)
    pressure_score: Decimal | None = Field(default=None, ge=0)
    shock_status: str | None = None
    explanation: str | None = None
    affected_sources: list[str] = Field(default_factory=list)
    affected_routes: list[str] = Field(default_factory=list)
    model_version: str
    event_timestamp: datetime


class IntelligenceEventOut(IntelligenceEventIn):
    id: int
