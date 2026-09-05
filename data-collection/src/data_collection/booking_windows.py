from datetime import date, timedelta


SUPPORTED_BOOKING_WINDOWS = (1, 7, 15, 30, 45)


def get_travel_date(observation_date: date, booking_window: int) -> date:
    """
    Calculate the travel date for a supported booking window.

    Example:
        observation_date = 2026-09-04
        booking_window = 7

        returns 2026-09-11
    """
    if booking_window not in SUPPORTED_BOOKING_WINDOWS:
        raise ValueError(
            f"Unsupported booking window: T+{booking_window}. "
            f"Supported windows are T+1, T+7, T+15, T+30 and T+45."
        )

    return observation_date + timedelta(days=booking_window)