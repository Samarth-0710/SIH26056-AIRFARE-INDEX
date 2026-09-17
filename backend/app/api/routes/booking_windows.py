from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.common import BookingWindow
from app.schemas.index import IndexHistoryOut
from app.services.index_service import index_history

router = APIRouter(prefix="/booking-windows", tags=["Booking windows"])

@router.get("", response_model=list[str])
def get_booking_windows():
    return [window.value for window in BookingWindow]

@router.get("/matrix", response_model=list[dict])
def get_booking_windows_matrix(db: Session = Depends(get_db)):
    """Retrieve corridor x booking window elementary index matrix for heatmaps."""
    from sqlalchemy import select, desc
    from app.db.models import Route, RouteIndex, IndexResult

    routes = db.scalars(select(Route).order_by(Route.code)).all()
    matrix = []

    for r in routes:
        row_data = {"route": r.code}
        for bw in BookingWindow:
            pair = db.execute(
                select(RouteIndex.index_value)
                .join(IndexResult, RouteIndex.index_result_id == IndexResult.id)
                .where(RouteIndex.route_id == r.id, IndexResult.booking_window == bw.value, IndexResult.status == "SUCCESS")
                .order_by(desc(IndexResult.observation_date), desc(IndexResult.calculation_timestamp))
            ).first()
            val = float(pair[0]) if pair and pair[0] is not None else 100.0
            row_data[bw.value] = round(val, 1)
        matrix.append(row_data)

    return matrix

@router.get("/{booking_window}/index", response_model=IndexHistoryOut)
def get_window_index(booking_window: BookingWindow, db: Session = Depends(get_db)):
    return IndexHistoryOut(items=index_history(db, None, None, booking_window.value))
