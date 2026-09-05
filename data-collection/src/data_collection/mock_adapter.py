from datetime import date, datetime, time

from .adapters import SourceAdapter
from .booking_windows import (
    SUPPORTED_BOOKING_WINDOWS,
    get_travel_date,
)
from .models import RawFareRecord


class MockFareAdapter(SourceAdapter):
    """
    Demo adapter used for development and testing.

    This does not connect to a real airline or OTA.
    """

    def collect(
        self,
        origin: str,
        destination: str,
        travel_date: date,
    ) -> list[RawFareRecord]:
        """
        Collect one demo fare record for a route and
        travel date.
        """

        observation_date = date.today()

        lead_days = (
            travel_date - observation_date
        ).days

        return [
            RawFareRecord(
                origin=origin,
                destination=destination,
                travel_date=travel_date,
                observation_date=observation_date,
                booking_window=lead_days,
                airline="DemoAir",
                flight_number="DA101",
                departure_time=time(7, 30),
                cabin_class="ECONOMY",
                fare_type="SAVER",
                baggage_characteristics="15KG",
                fare_amount=5400.0,
                currency="INR",
                source="mock",
                observation_timestamp=datetime.now(),
            )
        ]

    def collect_all_windows(
        self,
        origin: str,
        destination: str,
        observation_date: date | None = None,
    ) -> list[RawFareRecord]:
        """
        Collect one demo fare record for each supported
        booking window.
        """

        if observation_date is None:
            observation_date = date.today()

        records = []

        for booking_window in SUPPORTED_BOOKING_WINDOWS:

            travel_date = get_travel_date(
                observation_date,
                booking_window,
            )

            record = RawFareRecord(
                origin=origin,
                destination=destination,
                travel_date=travel_date,
                observation_date=observation_date,
                booking_window=booking_window,
                airline="DemoAir",
                flight_number="DA101",
                departure_time=time(7, 30),
                cabin_class="ECONOMY",
                fare_type="SAVER",
                baggage_characteristics="15KG",
                fare_amount=5400.0,
                currency="INR",
                source="mock",
                observation_timestamp=datetime.now(),
            )

            records.append(record)

        return records