from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.simulation import SimulationRequest, SimulationResponse
from app.services.simulation_service import create_simulation

router = APIRouter(prefix="/simulation", tags=["Policy simulation"])

@router.post("", response_model=SimulationResponse, status_code=201)
def post_simulation(payload: SimulationRequest, db: Session = Depends(get_db)):
    return create_simulation(db, payload)
