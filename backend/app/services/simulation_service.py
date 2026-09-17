from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.db.models import IndexResult, RouteIndex, SimulationResult
from app.schemas.simulation import SimulationRequest, SimulationResponse
from .helpers import require_route


def create_simulation(db: Session, payload: SimulationRequest) -> SimulationResponse:
    route = require_route(db, payload.route)
    current = db.scalars(select(IndexResult).where(IndexResult.status == "SUCCESS").order_by(
        desc(IndexResult.observation_date), desc(IndexResult.calculation_timestamp))).first()
    if current is None:
        raise HTTPException(409, "simulation unavailable: no official index result is stored")

    shock_decimal = Decimal(str(payload.shock_percent))
    if payload.projected_index is not None:
        projected = Decimal(str(payload.projected_index))
        impact = projected - current.index_value if current.index_value is not None else None
    else:
        # Calculate impact from route weight and shock percentage:
        # ΔI = I_current * (shock_percent / 100) * route_weight
        route_idx = db.scalars(
            select(RouteIndex)
            .where(RouteIndex.route_id == route.id)
            .order_by(desc(RouteIndex.index_result_id))
        ).first()
        if route_idx and route_idx.weight is not None:
            route_weight = route_idx.weight
        else:
            try:
                from statistical_engine.models.weights import get_demo_reference_weights
                demo_weights = get_demo_reference_weights().weights
                route_weight = Decimal(str(demo_weights.get(route.code, 0.10)))
            except Exception:
                route_weight = Decimal("0.10")

        base_val = current.index_value or Decimal("100.0")
        shock_mult = shock_decimal / Decimal("100")
        impact = round(base_val * route_weight * shock_mult, 4)
        projected = round(base_val + impact, 4)

    row = SimulationResult(
        route_id=route.id,
        shock_percent=payload.shock_percent,
        current_index=current.index_value,
        projected_index=projected,
        impact_points=impact,
        status="SIMULATED",
        input_metadata=payload.input_metadata,
    )
    db.add(row)
    db.commit()
    return SimulationResponse(
        current_index=current.index_value,
        route=route.code,
        shock_percent=payload.shock_percent,
        projected_index=projected,
        impact_points=impact,
        status="SIMULATED",
    )
