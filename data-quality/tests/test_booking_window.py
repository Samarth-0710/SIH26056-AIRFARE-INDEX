"""
Tests for booking-window calculation.
"""

from datetime import date, datetime

import pytest

from data_quality.booking_window import (
    calculate_lead_days,
    calculate_booking_window,
    is_supported_lead_time,
)
from data_quality.models import BookingWindow


def test_t_plus_1():
    result = calculate_booking_window(
        date(2026, 9, 1),
        date(2026, 9, 2),
    )

    assert result == BookingWindow.T_1


def test_t_plus_7():
    result = calculate_booking_window(
        date(2026, 9, 1),
        date(2026, 9, 8),
    )

    assert result == BookingWindow.T_7


def test_t_plus_15():
    result = calculate_booking_window(
        date(2026, 9, 1),
        date(2026, 9, 16),
    )

    assert result == BookingWindow.T_15


def test_t_plus_30():
    result = calculate_booking_window(
        date(2026, 9, 1),
        date(2026, 10, 1),
    )

    assert result == BookingWindow.T_30


def test_t_plus_45():
    result = calculate_booking_window(
        date(2026, 9, 1),
        date(2026, 10, 16),
    )

    assert result == BookingWindow.T_45


def test_calculate_lead_days():
    result = calculate_lead_days(
        date(2026, 9, 1),
        date(2026, 9, 8),
    )

    assert result == 7


def test_datetime_values_are_supported():
    result = calculate_booking_window(
        datetime(2026, 9, 1, 10, 30),
        datetime(2026, 9, 8, 18, 45),
    )

    assert result == BookingWindow.T_7


@pytest.mark.parametrize(
    "lead_days",
    [0, 2, 6, 8, 14, 16, 29, 31, 44, 46, -1],
)
def test_unsupported_lead_times(lead_days):
    assert is_supported_lead_time(lead_days) is False


def test_unsupported_booking_window_raises_error():
    with pytest.raises(ValueError):
        calculate_booking_window(
            date(2026, 9, 1),
            date(2026, 9, 7),
        )


def test_travel_date_before_observation_date():
    with pytest.raises(ValueError):
        calculate_booking_window(
            date(2026, 9, 10),
            date(2026, 9, 9),
        )