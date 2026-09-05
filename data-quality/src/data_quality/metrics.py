"""
Data-quality metrics for SIH26056.

This module measures:
- route coverage
- source coverage
- booking-window coverage
- quality-status distribution
- observation freshness

These metrics help the team understand how complete and
up-to-date the collected airfare data is.

This module does NOT:
- calculate the Airfare Price Index
- calculate statistical weights
- remove observations
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Iterable

from .models import (
    BookingWindow,
    NormalizedFareObservation,
    QualityStatus,
)


def calculate_route_coverage(
    observations: Iterable[NormalizedFareObservation],
    expected_routes: set[str],
) -> float:
    """
    Calculate the percentage of expected routes observed.

    Returns a value between 0 and 1.

    Example:
        4 observed routes / 5 expected routes = 0.8
    """

    if not expected_routes:
        return 0.0

    observed_routes = {
        observation.route
        for observation in observations
        if observation.route
    }

    return len(
        observed_routes & expected_routes
    ) / len(expected_routes)


def calculate_source_coverage(
    observations: Iterable[NormalizedFareObservation],
    expected_sources: set[str],
) -> float:
    """
    Calculate the percentage of expected sources observed.

    Returns a value between 0 and 1.
    """

    if not expected_sources:
        return 0.0

    observed_sources = {
        observation.source
        for observation in observations
        if observation.source
    }

    return len(
        observed_sources & expected_sources
    ) / len(expected_sources)


def calculate_booking_window_coverage(
    observations: Iterable[NormalizedFareObservation],
    expected_windows: set[BookingWindow] | None = None,
) -> float:
    """
    Calculate the percentage of expected booking windows observed.

    Returns a value between 0 and 1.

    If expected_windows is not supplied, all five project
    booking windows are considered expected.
    """

    if expected_windows is None:
        expected_windows = set(BookingWindow)

    if not expected_windows:
        return 0.0

    observed_windows = {
        observation.booking_window
        for observation in observations
        if observation.booking_window is not None
    }

    return len(
        observed_windows & expected_windows
    ) / len(expected_windows)


def count_quality_statuses(
    observations: Iterable[NormalizedFareObservation],
) -> dict[str, int]:
    """
    Count observations by quality status.
    """

    counts = Counter(
        observation.quality_status.value
        for observation in observations
    )

    return {
        status.value: counts.get(status.value, 0)
        for status in QualityStatus
    }


def calculate_validity_rate(
    observations: Iterable[NormalizedFareObservation],
) -> float:
    """
    Calculate the percentage of observations marked VALID.

    Returns a value between 0 and 1.
    """

    observation_list = list(observations)

    if not observation_list:
        return 0.0

    valid_count = sum(
        observation.quality_status == QualityStatus.VALID
        for observation in observation_list
    )

    return valid_count / len(observation_list)


def calculate_freshness_minutes(
    observation: NormalizedFareObservation,
    current_time: datetime,
) -> float:
    """
    Calculate how old an observation is in minutes.

    current_time should normally be timezone-aware UTC.
    """

    observation_time = observation.observation_timestamp

    if observation_time.tzinfo is None:
        observation_time = observation_time.replace(
            tzinfo=timezone.utc
        )

    if current_time.tzinfo is None:
        current_time = current_time.replace(
            tzinfo=timezone.utc
        )

    difference = current_time - observation_time

    return difference.total_seconds() / 60


def calculate_average_freshness_minutes(
    observations: Iterable[NormalizedFareObservation],
    current_time: datetime,
) -> float:
    """
    Calculate the average observation age in minutes.

    Returns 0.0 when no observations are supplied.
    """

    observation_list = list(observations)

    if not observation_list:
        return 0.0

    freshness_values = [
        calculate_freshness_minutes(
            observation,
            current_time,
        )
        for observation in observation_list
    ]

    return sum(freshness_values) / len(
        freshness_values
    )