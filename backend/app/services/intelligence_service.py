from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.db.models import IntelligenceEvent
from app.schemas.intelligence import IntelligenceEventOut


def events(db: Session, shocks_only: bool) -> list[IntelligenceEventOut]:
    query = select(IntelligenceEvent).order_by(desc(IntelligenceEvent.event_timestamp))
    if shocks_only: query = query.where(IntelligenceEvent.event_type == "SHOCK")
    return [IntelligenceEventOut(id=e.id, route=e.route.code if e.route else None, event_type=e.event_type,
       anomaly_score=e.anomaly_score, pressure_score=e.pressure_score, shock_status=e.shock_status,
       explanation=e.explanation, affected_sources=e.affected_sources, affected_routes=e.affected_routes,
       model_version=e.model_version, event_timestamp=e.event_timestamp) for e in db.scalars(query).all()]
