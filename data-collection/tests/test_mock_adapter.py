from datetime import date

from data_collection.mock_adapter import MockFareAdapter


def test_mock_adapter_collects_raw_fare():
    adapter = MockFareAdapter()

    records = adapter.collect(
        origin="DEL",
        destination="BOM",
        travel_date=date(2026, 9, 11),
    )

    assert len(records) == 1

    record = records[0]

    assert record.origin == "DEL"
    assert record.destination == "BOM"
    assert record.airline == "DemoAir"
    assert record.source == "mock"
    assert record.currency == "INR"
    assert record.fare_amount > 0

def test_mock_adapter_collects_all_booking_windows():
    adapter = MockFareAdapter()

    records = adapter.collect_all_windows(
        origin="DEL",
        destination="BOM",
        observation_date=date(2026, 9, 4),
    )

    assert len(records) == 5

    booking_windows = [
        record.booking_window
        for record in records
    ]

    assert booking_windows == [1, 7, 15, 30, 45]