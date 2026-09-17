from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.db.models import IndexResult, Route, RouteIndex
from app.schemas.route import RouteContributionOut, RouteIndexOut, RouteOut
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


def list_route_contributions(db: Session, booking_window: str | None = None) -> list[RouteContributionOut]:
    window = booking_window or "T+15"
    latest_idx = db.scalars(
        select(IndexResult)
        .where(IndexResult.booking_window == window, IndexResult.status == "SUCCESS")
        .order_by(desc(IndexResult.observation_date), desc(IndexResult.calculation_timestamp))
    ).first()

    if latest_idx is None:
        latest_idx = db.scalars(
            select(IndexResult)
            .where(IndexResult.status == "SUCCESS")
            .order_by(desc(IndexResult.observation_date), desc(IndexResult.calculation_timestamp))
        ).first()

    if latest_idx is None:
        return []

    pairs = db.execute(
        select(RouteIndex, Route)
        .join(Route, RouteIndex.route_id == Route.id)
        .where(RouteIndex.index_result_id == latest_idx.id)
    ).all()

    total_point_contrib = sum(float(ri.contribution or 0.0) for ri, _ in pairs)
    results: list[RouteContributionOut] = []

    for ri, r in pairs:
        w = float(ri.weight) if ri.weight is not None else 0.1
        idx_val = float(ri.index_value) if ri.index_value is not None else 100.0
        lvl_contrib = round(w * idx_val, 2)
        pt_contrib = float(ri.contribution) if ri.contribution is not None else round(w * (idx_val - 100.0), 2)
        pct_share = round((pt_contrib / total_point_contrib) * 100, 1) if total_point_contrib != 0 else 0.0

        results.append(
            RouteContributionOut(
                route=r.code,
                weight=w,
                route_index=idx_val,
                level_contribution=lvl_contrib,
                point_contribution=pt_contrib,
                percentage_share_of_change=pct_share,
            )
        )

    results.sort(key=lambda x: x.level_contribution, reverse=True)
    return results
