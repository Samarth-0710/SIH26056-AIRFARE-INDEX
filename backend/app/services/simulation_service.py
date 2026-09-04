from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.db.models import IndexResult, SimulationResult
from app.schemas.simulation import SimulationRequest, SimulationResponse
from .helpers import require_route


def create_simulation(db: Session, payload: SimulationRequest) -> SimulationResponse:
    route = require_route(db, payload.route)
    current = db.scalars(select(IndexResult).where(IndexResult.status == "SUCCESS").order_by(
        desc(IndexResult.observation_date), desc(IndexResult.calculation_timestamp))).first()
    if current is None:
        raise HTTPException(409, "simulation unavailable: no official index result is stored")
    if payload.projected_index is None:
        raise HTTPException(422, "projected_index from an approved simulation component is required; backend does not invent projections")
    impact = payload.projected_index - current.index_value if current.index_value is not None else None
    row = SimulationResult(route_id=route.id, shock_percent=payload.shock_percent, current_index=current.index_value,
      projected_index=payload.projected_index, impact_points=impact, status="SIMULATED", input_metadata=payload.input_metadata)
    db.add(row); db.commit()
    return SimulationResponse(current_index=current.index_value, route=route.code, shock_percent=payload.shock_percent,
      projected_index=payload.projected_index, impact_points=impact, status="SIMULATED")
