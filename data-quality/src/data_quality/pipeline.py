"""
Data-quality processing pipeline for SIH26056.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from .duplicates import mark_duplicates
from .models import (
    NormalizedFareObservation,
    QualityStatus,
    RawFareObservation,
)
from .normalizer import normalize_fare_observation
from .outliers import mark_outliers
from .validators import classify_raw_observation


@dataclass
class PipelineResult:
    """
    Result returned by the data-quality pipeline.
    """

    normalized_observations: List[
        NormalizedFareObservation
    ] = field(default_factory=list)

    rejected_observations: List[
        RawFareObservation
    ] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """
        Return the total number of raw observations processed.

        Both accepted and rejected observations are included.
        """

        return (
            len(self.normalized_observations)
            + len(self.rejected_observations)
        )

    @property
    def valid_count(self) -> int:
        """
        Return the number of normalized observations currently
        classified as VALID.
        """

        return sum(
            1
            for observation in self.normalized_observations
            if observation.quality_status
            == QualityStatus.VALID
        )

    @property
    def excluded_count(self) -> int:
        """
        Return the number of observations excluded from processing.

        This includes:
        - rejected raw observations
        - normalized observations later marked EXCLUDED,
          such as exact duplicates
        """

        rejected_count = len(
            self.rejected_observations
        )

        normalized_excluded_count = sum(
            1
            for observation in self.normalized_observations
            if observation.quality_status
            == QualityStatus.EXCLUDED
        )

        return (
            rejected_count
            + normalized_excluded_count
        )

    @property
    def outlier_count(self) -> int:
        """
        Return the number of normalized observations flagged
        as OUTLIER.
        """

        return sum(
            1
            for observation in self.normalized_observations
            if observation.quality_status
            == QualityStatus.OUTLIER
        )


# ---------------------------------------------------------------------------
# Single observation
# ---------------------------------------------------------------------------

def process_observation(
    observation: RawFareObservation,
) -> tuple[
    Optional[NormalizedFareObservation],
    Optional[RawFareObservation],
]:
    """
    Process one raw observation.

    Returns:

        (normalized, None)
            when accepted

        (None, raw_observation)
            when rejected
    """

    status, reason = classify_raw_observation(
        observation
    )

    # Any raw observation classified as EXCLUDED is rejected by
    # the pipeline and preserved separately.
    #
    # This includes:
    # - cancelled
    # - sold out
    # - unavailable
    # - missing data
    # - invalid fare
    # - unknown source
    # - invalid date
    if status == QualityStatus.EXCLUDED:
        observation.metadata[
            "quality_status"
        ] = status.value

        observation.metadata[
            "quality_reason"
        ] = reason

        return None, observation

    try:
        normalized = normalize_fare_observation(
            observation
        )

    except (ValueError, TypeError) as error:
        observation.metadata[
            "quality_status"
        ] = QualityStatus.EXCLUDED.value

        observation.metadata[
            "quality_reason"
        ] = str(error)

        return None, observation

    # If normalization itself produced an excluded observation,
    # preserve it as rejected rather than passing it downstream.
    if normalized.quality_status == QualityStatus.EXCLUDED:
        observation.metadata[
            "quality_status"
        ] = normalized.quality_status.value

        observation.metadata[
            "quality_reason"
        ] = normalized.quality_reason

        return None, observation

    return normalized, None


# ---------------------------------------------------------------------------
# Multiple observations
# ---------------------------------------------------------------------------

def process_observations(
    observations: Iterable[RawFareObservation],
) -> PipelineResult:
    """
    Process multiple raw observations.
    """

    normalized_observations = []
    rejected_observations = []

    for observation in observations:
        normalized, rejected = process_observation(
            observation
        )

        if normalized is not None:
            normalized_observations.append(
                normalized
            )

        if rejected is not None:
            rejected_observations.append(
                rejected
            )

    # -----------------------------------------------------------------------
    # Duplicate detection
    # -----------------------------------------------------------------------

    normalized_observations = mark_duplicates(
        normalized_observations
    )

    # -----------------------------------------------------------------------
    # Outlier detection
    # -----------------------------------------------------------------------

    # Only currently VALID observations are passed to the IQR calculation.
    # Excluded duplicates therefore do not affect the outlier bounds.
    valid_for_outlier_detection = [
        observation
        for observation in normalized_observations
        if observation.quality_status
        == QualityStatus.VALID
    ]

    if valid_for_outlier_detection:
        mark_outliers(
            valid_for_outlier_detection
        )

    return PipelineResult(
        normalized_observations=normalized_observations,
        rejected_observations=rejected_observations,
    )


# ---------------------------------------------------------------------------
# Public pipeline API
# ---------------------------------------------------------------------------

def run_pipeline(
    observations: Iterable[RawFareObservation],
) -> PipelineResult:
    """
    Run the complete data-quality pipeline.
    """

    return process_observations(
        observations
    )