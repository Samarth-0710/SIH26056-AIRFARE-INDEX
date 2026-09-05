from datetime import date

from data_collection.ignav_adapter import IgnavFareAdapter
from data_collection.booking_windows import SUPPORTED_BOOKING_WINDOWS


def test_ignav_blr_del_all_booking_windows():
    adapter = IgnavFareAdapter()

    observation_date = date.today()

    for booking_window in SUPPORTED_BOOKING_WINDOWS:

        print(
            f"\n{'=' * 70}"
        )

        print(
            f"BLR -> DEL | T+{booking_window}"
        )

        print(
            f"{'=' * 70}"
        )

        records = adapter.collect_route_window(
            origin="BLR",
            destination="DEL",
            observation_date=observation_date,
            booking_window=booking_window,
        )

        print(
            f"\nTotal records: {len(records)}\n"
        )

        assert records

        for i, record in enumerate(
            records,
            start=1,
        ):

            print(
                f"{i}. "
                f"{record.airline} | "
                f"Flight: {record.flight_number} | "
                f"Departure: {record.departure_time} | "
                f"Fare: ₹{record.fare_amount:.2f} | "
                f"Currency: {record.currency} | "
                f"Cabin: {record.cabin_class} | "
                f"Baggage: {record.baggage_characteristics}"
            )

            assert record.origin == "BLR"
            assert record.destination == "DEL"
            assert record.booking_window == booking_window
            assert record.fare_amount > 0
            assert record.currency == "INR"
            assert record.source == "ignav"
            assert record.fare_type == "UNKNOWN"