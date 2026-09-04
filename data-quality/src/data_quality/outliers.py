"""
Outlier detection for SIH26056.

This module identifies unusually high or low comparable fares
using the Interquartile Range (IQR) method.

Important:
- Outlier detection is a quality flag.
- Observations are NOT deleted.
- The threshold is configurable.
- This is an engineering quality rule, not an official
  MoSPI index methodology rule.
"""

from __future__ import annotations

from typing import Iterable

from .models import (
    NormalizedFareObservation,
    QualityStatus,
)


def calculate_iqr_bounds(
    values: list[float],
    multiplier: float = 1.5,
) -> tuple[float, float]:
    """
    Calculate lower and upper IQR bounds.

    Bounds:
        lower = Q1 - multiplier * IQR
        upper = Q3 + multiplier * IQR

    A multiplier of 1.5 is the conventional IQR rule.
    """

    if not values:
        raise ValueError("At least one value is required.")

    if multiplier < 0:
        raise ValueError("Multiplier cannot be negative.")

    sorted_values = sorted(values)

    q1 = _percentile(sorted_values, 25)
    q3 = _percentile(sorted_values, 75)

    iqr = q3 - q1

    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    return lower_bound, upper_bound


def _percentile(
    sorted_values: list[float],
    percentile: float,
) -> float:
    """Calculate a percentile using linear interpolation."""

    if not sorted_values:
        raise ValueError("Values cannot be empty.")

    if not 0 <= percentile <= 100:
        raise ValueError(
            "Percentile must be between 0 and 100."
        )

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (
        (len(sorted_values) - 1)
        * percentile
        / 100
    )

    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(sorted_values) - 1,
    )

    fraction = position - lower_index

    return (
        sorted_values[lower_index]
        + fraction
        * (
            sorted_values[upper_index]
            - sorted_values[lower_index]
        )
    )


def find_outlier_indices(
    observations: Iterable[NormalizedFareObservation],
    multiplier: float = 1.5,
) -> list[int]:
    """
    Return indexes of observations whose comparable fares
    fall outside the IQR bounds.

    Observations with missing or non-positive comparable fares
    are ignored here because they should already be handled
    by the validation stage.
    """

    observation_list = list(observations)

    valid_items = [
        (index, observation)
        for index, observation in enumerate(observation_list)
        if observation.comparable_fare is not None
        and observation.comparable_fare > 0
    ]

    if len(valid_items) < 4:
        return []

    values = [
        observation.comparable_fare
        for _, observation in valid_items
    ]

    lower_bound, upper_bound = calculate_iqr_bounds(
        values,
        multiplier=multiplier,
    )

    return [
        index
        for index, observation in valid_items
        if (
            observation.comparable_fare < lower_bound
            or observation.comparable_fare > upper_bound
        )
    ]


def mark_outliers(
    observations: list[NormalizedFareObservation],
    multiplier: float = 1.5,
) -> list[NormalizedFareObservation]:
    """
    Mark detected outliers as OUTLIER.

    The original observation remains in the list.
    """

    outlier_indices = find_outlier_indices(
        observations,
        multiplier=multiplier,
    )

    for index in outlier_indices:
        observations[index].quality_status = (
            QualityStatus.OUTLIER
        )
        observations[index].quality_reason = (
            "comparable fare flagged as an IQR outlier"
        )

    return observations


def count_outliers(
    observations: Iterable[NormalizedFareObservation],
    multiplier: float = 1.5,
) -> int:
    """Return the number of detected outliers."""

    return len(
        find_outlier_indices(
            observations,
            multiplier=multiplier,
        )
    )