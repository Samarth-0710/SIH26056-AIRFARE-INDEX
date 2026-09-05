"""
Duplicate detection for SIH26056.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple

from .models import (
    NormalizedFareObservation,
    QualityStatus,
)


def duplicate_key(
    observation: NormalizedFareObservation,
) -> Tuple[str, object, str]:
    """
    Build the exact duplicate key.

    Source and observation timestamp are included so that the same
    fare observed at a different time is not treated as an exact
    duplicate.
    """

    return (
        observation.fingerprint,
        observation.observation_timestamp,
        observation.source,
    )


def find_duplicate_indices(
    observations: Iterable[
        NormalizedFareObservation
    ],
) -> List[int]:
    """
    Return indices of duplicate observations.

    The first occurrence is retained.
    Later exact duplicates are returned.
    """

    seen = set()
    duplicate_indices = []

    for index, observation in enumerate(observations):
        key = duplicate_key(observation)

        if key in seen:
            duplicate_indices.append(index)
        else:
            seen.add(key)

    return duplicate_indices


def is_duplicate(
    observation: NormalizedFareObservation,
    existing_keys: set,
) -> bool:
    """Check whether an observation's duplicate key already exists."""

    return duplicate_key(observation) in existing_keys


def mark_duplicates(
    observations: Iterable[
        NormalizedFareObservation
    ],
) -> List[NormalizedFareObservation]:
    """
    Mark later exact duplicate observations as EXCLUDED.

    Observations are not deleted.
    """

    observations = list(observations)

    seen = set()

    for observation in observations:
        key = duplicate_key(observation)

        if key in seen:
            observation.quality_status = (
                QualityStatus.EXCLUDED
            )
            observation.quality_reason = (
                "exact duplicate observation"
            )

            observation.metadata[
                "quality_reason_code"
            ] = "DUPLICATE"

        else:
            seen.add(key)

    return observations
def count_duplicates(
    observations: Iterable[
        NormalizedFareObservation
    ],
) -> int:
    """Return the number of duplicate observations."""

    return len(
        find_duplicate_indices(observations)
    )
