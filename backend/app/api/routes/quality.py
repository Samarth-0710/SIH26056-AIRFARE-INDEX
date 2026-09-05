from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.quality import QualityMetricOut
from app.services.quality_service import quality_metrics

router = APIRouter(prefix="/quality", tags=["Data quality"])

@router.get("", response_model=list[QualityMetricOut])
def get_quality(route: str | None = None, source: str | None = None, db: Session = Depends(get_db)):
    return quality_metrics(db, route, source)
