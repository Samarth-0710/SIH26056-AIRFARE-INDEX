"""
End-to-end data-quality pipeline for SIH26056.

Pipeline:

Raw Fare Observation
        ↓
Validation
        ↓
Normalization
        ↓
Duplicate Detection
        ↓
Outlier Detection
        ↓
Normalized + Quality-Controlled Observations

This module coordinates the data-quality components.
It does NOT calculate the Airfare Price Index.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .duplicates import find_duplicate_indices
from .models import (
    NormalizedFareObservation,
    QualityStatus,
    RawFareObservation,
)
from .normalizer import normalize_fare_observation
from .outliers import find_outlier_indices
from .validators import classify_raw_observation


@dataclass
class PipelineResult:
    """
    Result returned by the data-quality pipeline.

    normalized_observations:
        Successfully normalized observations, including those
        flagged as EXCLUDED or OUTLIER.

    rejected_observations:
        Raw observations that could not be normalized because
        required information was missing or invalid.
    """

    normalized_observations: list[
        NormalizedFareObservation
    ]

    rejected_observations: list[
        RawFareObservation
    ]

    @property
    def total_processed(self) -> int:
        """Return the total number of raw observations processed."""

        return (
            len(self.normalized_observations)
            + len(self.rejected_observations)
        )

    @property
    def valid_count(self) -> int:
        """Return the number of observations currently marked VALID."""

        return sum(
            observation.quality_status == QualityStatus.VALID
            for observation in self.normalized_observations
        )

    @property
    def excluded_count(self) -> int:
        """Return the number of observations marked EXCLUDED."""

        return sum(
            observation.quality_status == QualityStatus.EXCLUDED
            for observation in self.normalized_observations
        ) + len(self.rejected_observations)

    @property
    def outlier_count(self) -> int:
        """Return the number of observations marked OUTLIER."""

        return sum(
            observation.quality_status == QualityStatus.OUTLIER
            for observation in self.normalized_observations
        )


def process_observation(
    observation: RawFareObservation,
) -> tuple[
    NormalizedFareObservation | None,
    RawFareObservation | None,
]:
    """
    Validate and normalize one raw observation.

    Returns:
        (normalized_observation, None)
            when the record can be normalized.

        (None, raw_observation)
            when validation fails before normalization.
    """

    status, reason = classify_raw_observation(
        observation
    )

    if status == QualityStatus.EXCLUDED:
        return None, observation

    try:
        normalized = normalize_fare_observation(
            observation
        )
    except (ValueError, TypeError):
        return None, observation

    normalized.quality_status = status
    normalized.quality_reason = reason

    return normalized, None


def run_pipeline(
    observations: Iterable[RawFareObservation],
    outlier_multiplier: float = 1.5,
) -> PipelineResult:
    """
    Run the complete data-quality pipeline.

    Processing order:

    1. Validate raw observations
    2. Normalize valid observations
    3. Detect exact duplicates
    4. Detect statistical outliers

    Observations are retained and classified rather than
    silently deleted.
    """

    normalized_observations: list[
        NormalizedFareObservation
    ] = []

    rejected_observations: list[
        RawFareObservation
    ] = []

    # ---------------------------------------------------------
    # Step 1 + 2: Validation and normalization
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Step 3: Duplicate detection
    # ---------------------------------------------------------

    duplicate_indices = find_duplicate_indices(
        normalized_observations
    )

    for index in duplicate_indices:
        normalized_observations[
            index
        ].quality_status = QualityStatus.EXCLUDED

        normalized_observations[
            index
        ].quality_reason = (
            "exact duplicate observation"
        )

    # ---------------------------------------------------------
    # Step 4: Outlier detection
    # ---------------------------------------------------------
    #
    # Only observations that are still VALID are considered
    # for outlier detection.
    #
    # EXCLUDED observations, including duplicates, must not
    # influence the IQR calculation.

    valid_observations = [
        observation
        for observation in normalized_observations
        if observation.quality_status == QualityStatus.VALID
    ]

    valid_indices = [
        index
        for index, observation in enumerate(
            normalized_observations
        )
        if observation.quality_status == QualityStatus.VALID
    ]

    valid_outlier_indices = find_outlier_indices(
        valid_observations,
        multiplier=outlier_multiplier,
    )

    # Convert indexes from the filtered VALID list back to
    # indexes in the original normalized observation list.
    outlier_indices = [
        valid_indices[index]
        for index in valid_outlier_indices
    ]

    for index in outlier_indices:
        normalized_observations[
            index
        ].quality_status = QualityStatus.OUTLIER

        normalized_observations[
            index
        ].quality_reason = (
            "comparable fare flagged as an IQR outlier"
        )

    return PipelineResult(
        normalized_observations=normalized_observations,
        rejected_observations=rejected_observations,
    )