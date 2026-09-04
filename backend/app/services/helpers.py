from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Route
from app.schemas.common import validate_route


def get_or_create_route(db: Session, route_code: str) -> Route:
    route_code = validate_route(route_code)
    route = db.scalar(select(Route).where(Route.code == route_code))
    if route is None:
        route = Route(code=route_code, origin=route_code[:3], destination=route_code[4:])
        db.add(route)
        db.flush()
    return route


def require_route(db: Session, route_code: str) -> Route:
    try:
        normalized_route = validate_route(route_code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    route = db.scalar(select(Route).where(Route.code == normalized_route))
    if route is None:
        raise HTTPException(status_code=404, detail="route not found")
    return route
