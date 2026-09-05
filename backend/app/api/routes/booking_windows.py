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

@router.get("/{booking_window}/index", response_model=IndexHistoryOut)
def get_window_index(booking_window: BookingWindow, db: Session = Depends(get_db)):
    return IndexHistoryOut(items=index_history(db, None, None, booking_window.value))
