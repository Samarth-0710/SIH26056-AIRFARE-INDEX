from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.validation import ValidationResultOut
from app.services.validation_service import get_validation_analysis

router = APIRouter(prefix="/validation", tags=["Statistical Validation"])


@router.get("", response_model=ValidationResultOut)
def get_validation_endpoint(db: Session = Depends(get_db)):
    """Retrieve statistical validation metrics and reference comparison.

    Adheres strictly to the Non-Fabrication Rule: does not fabricate false
    government/DGCA series when an official stream is not connected.
    """
    return get_validation_analysis(db)
