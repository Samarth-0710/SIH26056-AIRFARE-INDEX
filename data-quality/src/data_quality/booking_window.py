"""
Booking-window calculation for SIH26056.

The project requires the following booking windows:
T+1, T+7, T+15, T+30, T+45.

This module calculates the exact lead time between the observation
date and travel date. Only the documented booking windows are accepted.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Union

from .models import BookingWindow


DateLike = Union[date, datetime]


SUPPORTED_LEAD_DAYS = {
    1: BookingWindow.T_1,
    7: BookingWindow.T_7,
    15: BookingWindow.T_15,
    30: BookingWindow.T_30,
    45: BookingWindow.T_45,
}


def _to_date(value: DateLike) -> date:
    """
    Convert a date or datetime into a date.

    Datetimes are converted using their existing date component.
    Timezone conversion should be performed before calling this
    function when timezone-aware timestamps are used.
    """
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    raise TypeError(
        "Expected a date or datetime value."
    )


def calculate_lead_days(
    observation_date: DateLike,
    travel_date: DateLike,
) -> int:
    """
    Calculate the exact number of calendar days between
    observation date and travel date.

    Example:
        observation_date = 2026-09-01
        travel_date      = 2026-09-08

        result = 7
    """
    observed = _to_date(observation_date)
    travel = _to_date(travel_date)

    return (travel - observed).days


def calculate_booking_window(
    observation_date: DateLike,
    travel_date: DateLike,
) -> BookingWindow:
    """
    Determine the project's booking window from exact lead time.

    Supported values:
        1  -> T+1
        7  -> T+7
        15 -> T+15
        30 -> T+30
        45 -> T+45

    Raises:
        ValueError: if the lead time is not one of the supported
                    project booking windows.
        TypeError: if the supplied values are not dates/datetimes.
    """
    lead_days = calculate_lead_days(
        observation_date,
        travel_date,
    )

    try:
        return SUPPORTED_LEAD_DAYS[lead_days]
    except KeyError:
        raise ValueError(
            f"Lead time of {lead_days} days does not match a "
            "supported booking window. "
            "Expected one of: T+1, T+7, T+15, T+30, T+45."
        ) from None


def is_supported_lead_time(lead_days: int) -> bool:
    """
    Check whether an exact lead time is supported by the project.
    """
    return lead_days in SUPPORTED_LEAD_DAYS