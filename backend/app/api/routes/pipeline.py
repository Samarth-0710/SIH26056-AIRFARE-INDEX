"""API endpoints for triggering and checking the SIH26056 pipeline."""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import IndexResult
from app.services.pipeline_service import run_pipeline as execute_pipeline

router = APIRouter(prefix="/pipeline", tags=["Pipeline Execution"])


class PipelineRunRequest(BaseModel):
    target_date: Optional[date] = None
    use_live_source: bool = False
    price_movement_pct: float = Field(default=2.5, description="Simulated daily price change percentage for demo execution")


@router.post("/run", status_code=status.HTTP_200_OK)
def run_pipeline_endpoint(
    payload: Optional[PipelineRunRequest] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Execute the end-to-end SIH26056 pipeline.

    Collects/prepares raw records -> cleans with Data Quality -> calculates with Statistical Engine
    -> evaluates with Intelligence -> stores all results in the Database.
    """
    req = payload or PipelineRunRequest()
    result = execute_pipeline(
        db=db,
        target_date=req.target_date,
        use_live_source=req.use_live_source,
        price_movement_pct=req.price_movement_pct,
    )
    return result


@router.get("/status")
def get_pipeline_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Check the latest pipeline execution and index results in the database."""
    latest_idx = db.scalars(
        select(IndexResult)
        .order_by(desc(IndexResult.observation_date), desc(IndexResult.calculation_timestamp))
    ).first()

    if latest_idx is None:
        return {
            "status": "IDLE",
            "message": "Pipeline has not run yet or database has no index results.",
            "latest_calculation": None,
        }

    return {
        "status": "ACTIVE",
        "latest_observation_date": latest_idx.observation_date.isoformat(),
        "latest_booking_window": latest_idx.booking_window,
        "latest_index_value": float(latest_idx.index_value) if latest_idx.index_value is not None else None,
        "calculation_version": latest_idx.calculation_version,
        "calculation_timestamp": latest_idx.calculation_timestamp.isoformat() if latest_idx.calculation_timestamp else None,
        "execution_checksum": latest_idx.execution_checksum,
    }


@router.get("/live-status")
def get_live_adapter_status(force_check: bool = False) -> Dict[str, Any]:
    """Check availability and genuine runtime connectivity of the live Ignav adapter."""
    try:
        from data_collection.ignav_adapter import IgnavFareAdapter
        from data_collection.adapters import SourceStatus

        adapter = IgnavFareAdapter()
        if not adapter.api_key:
            return {
                "source": "IGNAV",
                "is_configured": False,
                "is_connected": False,
                "status": "NOT_CONFIGURED",
                "message": "Live API credentials unconfigured; fallback active",
            }

        status_enum, message = adapter.check_connection(force_check=force_check)
        is_connected = status_enum == SourceStatus.AVAILABLE

        return {
            "source": "IGNAV",
            "is_configured": True,
            "is_connected": is_connected,
            "status": "CONNECTED" if is_connected else status_enum.value,
            "message": message,
        }
    except Exception as e:
        return {
            "source": "IGNAV",
            "is_configured": False,
            "is_connected": False,
            "status": "ERROR",
            "message": f"Live adapter error: {str(e)}",
        }
