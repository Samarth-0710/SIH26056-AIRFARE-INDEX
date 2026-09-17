from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.quality import QualityMetricOut
from app.services.quality_service import quality_metrics

router = APIRouter(prefix="/quality", tags=["Data quality"])

@router.get("", response_model=list[QualityMetricOut])
def get_quality(route: str | None = None, source: str | None = None, db: Session = Depends(get_db)):
    return quality_metrics(db, route, source)


@router.get("/summary", response_model=dict)
def get_quality_summary(db: Session = Depends(get_db)):
    """Retrieve summarized observation quality counts, filtering breakdown, and source health."""
    from sqlalchemy import func, select
    from app.db.models import FareObservation, QualityMetric

    # 1. Total observations stored
    total_obs = db.scalar(select(func.count(FareObservation.id))) or 0

    # 2. Count by quality_status
    status_counts = dict(
        db.execute(
            select(FareObservation.quality_status, func.count(FareObservation.id))
            .group_by(FareObservation.quality_status)
        ).all()
    )

    valid_count = status_counts.get("VALID", 0)
    suspect_count = status_counts.get("SUSPECT", 0)
    excluded_count = status_counts.get("EXCLUDED", 0)
    outlier_count = status_counts.get("OUTLIER", 0)

    # 3. Latest quality metric
    latest_qm = db.scalars(select(QualityMetric).order_by(QualityMetric.generated_at.desc())).first()
    route_cov = float(latest_qm.route_coverage) if latest_qm and latest_qm.route_coverage is not None else 1.0
    source_cov = float(latest_qm.source_coverage) if latest_qm and latest_qm.source_coverage is not None else 1.0
    freshness = latest_qm.freshness_minutes if latest_qm and latest_qm.freshness_minutes is not None else 1

    source_name = latest_qm.source if latest_qm and latest_qm.source else "MOCK"

    return {
        "total_observations": total_obs,
        "valid_observations": valid_count,
        "suspect_observations": suspect_count,
        "excluded_observations": excluded_count,
        "outlier_count": outlier_count,
        "route_coverage": route_cov,
        "source_coverage": source_cov,
        "freshness_minutes": freshness,
        "status": "OPTIMAL" if valid_count > 0 else "NO_DATA",
        "source_health": [
            {
                "source": source_name,
                "status": "HEALTHY",
                "last_collection": latest_qm.generated_at.isoformat() if latest_qm else None,
                "observation_count": total_obs,
                "coverage_percent": round(source_cov * 100, 1),
            }
        ],
    }
