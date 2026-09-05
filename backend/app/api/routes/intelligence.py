from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.intelligence import IntelligenceEventOut
from app.services.intelligence_service import events

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

@router.get("", response_model=list[IntelligenceEventOut])
def get_intelligence(db: Session = Depends(get_db)):
    return events(db, shocks_only=False)

@router.get("/shocks", response_model=list[IntelligenceEventOut])
def get_shocks(db: Session = Depends(get_db)):
    return events(db, shocks_only=True)
