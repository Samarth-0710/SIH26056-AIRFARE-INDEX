from datetime import date, datetime, time

from data_collection.models import RawFareRecord


def test_raw_fare_record_creation():
    record = RawFareRecord(
        origin="DEL",
        destination="BOM",
        travel_date=date(2026, 9, 5),
        observation_date=date(2026, 9, 4),
        booking_window=1,
        airline="IndiGo",
        flight_number="6E201",
        departure_time=time(7, 0),
        cabin_class="ECONOMY",
        fare_type="SAVER",
        baggage_characteristics="15KG",
        fare_amount=5400.0,
        currency="INR",
        source="demo",
        observation_timestamp=datetime(2026, 9, 4, 18, 0),
    )

    assert record.origin == "DEL"
    assert record.destination == "BOM"
    assert record.booking_window == 1
    assert record.fare_amount == 5400.0
    assert record.currency == "INR"
    assert record.source == "demo"