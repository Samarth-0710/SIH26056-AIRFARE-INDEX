from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.common import BookingWindow
from app.schemas.index import IndexHistoryOut, IndexResultOut
from app.services import index_service

router = APIRouter(prefix="/index", tags=["Official index"])

@router.get("/current", response_model=IndexResultOut)
def get_current_index(booking_window: BookingWindow | None = None, db: Session = Depends(get_db)):
    return index_service.current_index(db, booking_window.value if booking_window else None)

@router.get("/history", response_model=IndexHistoryOut)
def get_index_history(start: date | None = None, end: date | None = None,
                      booking_window: BookingWindow | None = None, db: Session = Depends(get_db)):
    return IndexHistoryOut(items=index_service.index_history(db, start, end, booking_window.value if booking_window else None))
