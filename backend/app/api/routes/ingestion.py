"""Internal integration endpoints for versioned upstream outputs. Protect with auth before deployment."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import FareObservation, IntelligenceEvent, QualityMetric
from app.schemas.index import IndexResultIn
from app.schemas.intelligence import IntelligenceEventIn, IntelligenceEventOut
from app.schemas.observation import FareObservationIn
from app.schemas.quality import QualityMetricIn, QualityMetricOut
from app.schemas.route import RouteIndexIn
from app.services.helpers import get_or_create_route
from app.services.index_service import store_index_result

router = APIRouter(prefix="/ingestion", tags=["Integration ingestion"])

@router.post("/index-results", status_code=status.HTTP_201_CREATED)
def ingest_index(payload: IndexResultIn, route_indices: list[RouteIndexIn], db: Session = Depends(get_db)):
    row = store_index_result(db, payload, route_indices)
    return {"id": row.id, "status": "stored"}

@router.post("/observations", status_code=status.HTTP_201_CREATED)
def ingest_observation(payload: FareObservationIn, db: Session = Depends(get_db)):
    route = get_or_create_route(db, f"{payload.origin}-{payload.destination}")
    row = FareObservation(route_id=route.id, **payload.model_dump(exclude={"origin", "destination", "booking_window", "metadata"}),
        booking_window=payload.booking_window.value, metadata_json=payload.metadata)
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "status": "stored"}

@router.post("/quality", response_model=QualityMetricOut, status_code=status.HTTP_201_CREATED)
def ingest_quality(payload: QualityMetricIn, db: Session = Depends(get_db)):
    route = get_or_create_route(db, payload.route) if payload.route else None
    row = QualityMetric(**payload.model_dump(exclude={"route"}), route_id=route.id if route else None)
    db.add(row); db.commit(); db.refresh(row)
    return QualityMetricOut(id=row.id, **payload.model_dump())

@router.post("/intelligence", response_model=IntelligenceEventOut, status_code=status.HTTP_201_CREATED)
def ingest_intelligence(payload: IntelligenceEventIn, db: Session = Depends(get_db)):
    route = get_or_create_route(db, payload.route) if payload.route else None
    row = IntelligenceEvent(**payload.model_dump(exclude={"route"}), route_id=route.id if route else None)
    db.add(row); db.commit(); db.refresh(row)
    return IntelligenceEventOut(id=row.id, **payload.model_dump())
