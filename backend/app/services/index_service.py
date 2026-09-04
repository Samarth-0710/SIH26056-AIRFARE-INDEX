from datetime import date
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.db.models import IndexResult, RouteIndex
from app.schemas.index import IndexResultIn, IndexResultOut
from app.schemas.route import RouteIndexIn
from .helpers import get_or_create_route


def _out(row: IndexResult, previous: IndexResult | None = None) -> IndexResultOut:
    current = row.index_value
    previous_value = previous.index_value if previous else None
    change = None
    if current is not None and previous_value not in (None, 0):
        change = (current - previous_value) / previous_value * Decimal("100")
    return IndexResultOut(index=current, previous_index=previous_value, change_percent=change,
        timestamp=row.calculation_timestamp, observation_date=row.observation_date,
        booking_window=row.booking_window, status=row.status,
        methodology_version=row.methodology_version, basket_version=row.basket_version,
        weight_version=row.weight_version, calculation_version=row.calculation_version,
        observation_set_version=row.observation_set_version, execution_checksum=row.execution_checksum)


def store_index_result(db: Session, payload: IndexResultIn, route_indices: list[RouteIndexIn]) -> IndexResult:
    exists = db.scalar(select(IndexResult).where(IndexResult.observation_date == payload.observation_date,
        IndexResult.booking_window == payload.booking_window.value,
        IndexResult.calculation_version == payload.calculation_version))
    if exists:
        raise HTTPException(409, "calculation version already exists; historical results are immutable")
    row = IndexResult(**payload.model_dump())
    row.booking_window = payload.booking_window.value
    db.add(row)
    db.flush()
    for item in route_indices:
        route = get_or_create_route(db, item.route)
        db.add(RouteIndex(index_result_id=row.id, route_id=route.id, index_value=item.index_value,
               status=item.status, weight=item.weight, contribution=item.contribution))
    db.commit()
    db.refresh(row)
    return row


def current_index(db: Session, booking_window: str | None) -> IndexResultOut:
    query = select(IndexResult).order_by(desc(IndexResult.observation_date), desc(IndexResult.calculation_timestamp))
    if booking_window:
        query = query.where(IndexResult.booking_window == booking_window)
    row = db.scalars(query).first()
    if row is None:
        raise HTTPException(404, "no official index result is available")
    previous = db.scalars(select(IndexResult).where(IndexResult.booking_window == row.booking_window,
        IndexResult.observation_date < row.observation_date).order_by(desc(IndexResult.observation_date))).first()
    return _out(row, previous)


def index_history(db: Session, start: date | None, end: date | None, booking_window: str | None) -> list[IndexResultOut]:
    if start and end and start > end:
        raise HTTPException(422, "start date must not be after end date")
    query = select(IndexResult).order_by(IndexResult.observation_date, IndexResult.calculation_timestamp)
    if start: query = query.where(IndexResult.observation_date >= start)
    if end: query = query.where(IndexResult.observation_date <= end)
    if booking_window: query = query.where(IndexResult.booking_window == booking_window)
    return [_out(row) for row in db.scalars(query).all()]
