"""
Duplicate detection for SIH26056.

This module identifies exact duplicate fare observations.

A record is considered an exact duplicate when the same:
- fare fingerprint
- observation timestamp
- source

appears more than once.

Repeated observations at different times are NOT duplicates.
"""

from __future__ import annotations

from typing import Iterable

from .models import (
    NormalizedFareObservation,
    QualityStatus,
)


def _duplicate_key(
    observation: NormalizedFareObservation,
) -> tuple[str, object, str]:
    """
    Build the key used to identify an exact duplicate.
    """

    return (
        observation.fingerprint,
        observation.observation_timestamp,
        observation.source,
    )


def find_duplicate_indices(
    observations: Iterable[NormalizedFareObservation],
) -> list[int]:
    """
    Return the indexes of observations that are exact duplicates.

    The first occurrence is kept.
    Later occurrences with the same duplicate key are returned.
    """

    seen: set[tuple[str, object, str]] = set()
    duplicate_indices: list[int] = []

    for index, observation in enumerate(observations):
        key = _duplicate_key(observation)

        if key in seen:
            duplicate_indices.append(index)
        else:
            seen.add(key)

    return duplicate_indices


def mark_duplicates(
    observations: list[NormalizedFareObservation],
) -> list[NormalizedFareObservation]:
    """
    Mark duplicate observations as EXCLUDED.

    The original observations are retained in the list.
    Only their quality status and reason are changed.
    """

    duplicate_indices = find_duplicate_indices(
        observations
    )

    for index in duplicate_indices:
        observations[index].quality_status = (
            QualityStatus.EXCLUDED
        )
        observations[index].quality_reason = (
            "exact duplicate observation"
        )

    return observations


def count_duplicates(
    observations: Iterable[NormalizedFareObservation],
) -> int:
    """
    Return the number of duplicate records.

    The first occurrence of a record is not counted as a duplicate.
    """

    return len(
        find_duplicate_indices(observations)
    )