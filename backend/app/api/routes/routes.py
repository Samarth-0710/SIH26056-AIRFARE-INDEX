from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.common import BookingWindow
from app.schemas.route import RouteIndexOut, RouteOut
from app.services import route_service

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.get("", response_model=list[RouteOut])
def get_routes(db: Session = Depends(get_db)):
    return route_service.list_routes(db)

@router.get("/{route}/index", response_model=RouteIndexOut)
def get_route_index(route: str, booking_window: BookingWindow | None = None, db: Session = Depends(get_db)):
    return route_service.route_index(db, route, booking_window.value if booking_window else None)
