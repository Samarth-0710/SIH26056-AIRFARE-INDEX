from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.db.models import QualityMetric, Route
from app.schemas.common import validate_route
from app.schemas.quality import QualityMetricOut


def quality_metrics(db: Session, route: str | None, source: str | None) -> list[QualityMetricOut]:
    query = select(QualityMetric).order_by(desc(QualityMetric.generated_at))
    if source: query = query.where(QualityMetric.source == source)
    if route:
        query = query.join(Route, QualityMetric.route_id == Route.id).where(Route.code == validate_route(route))
    return [QualityMetricOut(id=row.id, metric_date=row.metric_date, route=row.route.code if row.route else None, source=row.source,
      observation_count=row.observation_count, route_coverage=row.route_coverage, source_coverage=row.source_coverage,
      freshness_minutes=row.freshness_minutes, missing_observations=row.missing_observations,
      invalid_observations=row.invalid_observations, anomalous_valid_observations=row.anomalous_valid_observations,
      status=row.status, generated_at=row.generated_at) for row in db.scalars(query).all()]
