"""Data Quality and Fare Normalization module for SIH26056."""

from .models import (
    BookingWindow,
    NormalizedFareObservation,
    QualityStatus,
    RawFareObservation,
)
from .pipeline import PipelineResult, process_observation, process_observations, run_pipeline
from .bridge import (
    clean_and_convert_records,
    normalized_to_engine_observation,
    raw_record_to_raw_observation,
)

__all__ = [
    "BookingWindow",
    "NormalizedFareObservation",
    "QualityStatus",
    "RawFareObservation",
    "PipelineResult",
    "process_observation",
    "process_observations",
    "run_pipeline",
    "clean_and_convert_records",
    "normalized_to_engine_observation",
    "raw_record_to_raw_observation",
]
