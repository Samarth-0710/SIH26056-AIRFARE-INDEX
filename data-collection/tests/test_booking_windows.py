from datetime import date

import pytest

from data_collection.booking_windows import (
    SUPPORTED_BOOKING_WINDOWS,
    get_travel_date,
)


def test_supported_booking_windows():
    assert SUPPORTED_BOOKING_WINDOWS == (1, 7, 15, 30, 45)


def test_travel_date_for_booking_window():
    observation_date = date(2026, 9, 4)

    assert get_travel_date(observation_date, 1) == date(2026, 9, 5)
    assert get_travel_date(observation_date, 7) == date(2026, 9, 11)
    assert get_travel_date(observation_date, 15) == date(2026, 9, 19)
    assert get_travel_date(observation_date, 30) == date(2026, 10, 4)
    assert get_travel_date(observation_date, 45) == date(2026, 10, 19)


def test_unsupported_booking_window():
    with pytest.raises(ValueError):
        get_travel_date(date(2026, 9, 4), 10)