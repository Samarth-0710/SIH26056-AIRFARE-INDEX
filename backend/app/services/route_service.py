from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.db.models import IndexResult, Route, RouteIndex
from app.schemas.route import RouteIndexOut, RouteOut
from .helpers import require_route


def list_routes(db: Session) -> list[RouteOut]:
    return [RouteOut(route=r.code, origin=r.origin, destination=r.destination, active=r.active)
            for r in db.scalars(select(Route).order_by(Route.code)).all()]


def route_index(db: Session, route_code: str, booking_window: str | None) -> RouteIndexOut:
    route = require_route(db, route_code)
    query = (select(RouteIndex, IndexResult).join(IndexResult, RouteIndex.index_result_id == IndexResult.id)
             .where(RouteIndex.route_id == route.id).order_by(desc(IndexResult.observation_date), desc(IndexResult.calculation_timestamp)))
    if booking_window: query = query.where(IndexResult.booking_window == booking_window)
    pair = db.execute(query).first()
    if pair is None: raise HTTPException(404, "no official route index is available")
    ri, current = pair
    prior_q = (select(RouteIndex, IndexResult).join(IndexResult, RouteIndex.index_result_id == IndexResult.id)
        .where(RouteIndex.route_id == route.id, IndexResult.booking_window == current.booking_window,
               IndexResult.observation_date < current.observation_date).order_by(desc(IndexResult.observation_date)))
    prior = db.execute(prior_q).first()
    previous = prior[0].index_value if prior else None
    change = None if ri.index_value is None or previous in (None, 0) else (ri.index_value - previous) / previous * Decimal("100")
    return RouteIndexOut(route=route.code, index=ri.index_value, previous_index=previous, change_percent=change,
      weight=ri.weight, contribution=ri.contribution, timestamp=current.calculation_timestamp,
      booking_window=current.booking_window, status=ri.status)
