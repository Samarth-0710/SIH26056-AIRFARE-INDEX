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


class SyntheticFareAdapter(SourceAdapter):
    """
    Realistic canonical synthetic adapter for SIH demonstration and development.

    Generates a realistic multi-corridor, multi-window domestic airline fare dataset
    conforming strictly to the canonical observation contract.
    """

    DEFAULT_ROUTES = [
        ("DEL", "BOM", 0.25, 4800.0),
        ("BOM", "DEL", 0.25, 4850.0),
        ("DEL", "BLR", 0.15, 5200.0),
        ("BLR", "DEL", 0.15, 5150.0),
        ("BOM", "BLR", 0.10, 4100.0),
        ("BLR", "BOM", 0.10, 4150.0),
    ]

    WINDOW_LEAD_DAYS = [1, 7, 15, 30, 45]

    WINDOW_FARE_MULTIPLIERS = {
        1: 1.45,   # T+1: last minute surge
        7: 1.20,   # T+7: 1 week advance
        15: 1.05,  # T+15: 2 weeks advance baseline
        30: 0.95,  # T+30: 1 month advance
        45: 0.88,  # T+45: early bird saver
    }

    FLIGHTS = [
        ("IndiGo", "6E-201", time(6, 30), "SAVER", 1.00),
        ("Air India", "AI-102", time(11, 45), "REGULAR", 1.08),
        ("Akasa Air", "QP-303", time(18, 15), "SAVER", 0.96),
    ]

    @classmethod
    def calculate_deterministic_fare(
        cls,
        origin: str,
        destination: str,
        airline: str,
        booking_window: int,
        base_price: float,
        day_offset: int = 0,
        dow: int = 0,
        price_factor: float = 1.0,
    ) -> float:
        """
        Deterministic, multi-variate fare calculation representing real-world domestic aviation dynamics:
        1. Macro price drift (+0.14% per day)
        2. Day-of-week demand seasonality
        3. Booking window advance tier multiplier
        4. Booking window differential growth (close-in surges faster than early-bird)
        5. Corridor-specific demand elasticity (DEL-BOM metro trunk vs BOM-BLR)
        6. Localized demand shock on DEL-BOM (days 18-24) to trigger shock detector
        7. Airline tier multiplier
        """
        # 1. Macro drift (+0.14% / day)
        macro = 1.0 + 0.0014 * day_offset

        # 2. Day-of-week seasonality (Fri, Sun higher; Tue, Wed lower)
        dow_effects = {0: 1.015, 1: 0.980, 2: 0.980, 3: 1.000, 4: 1.030, 5: 1.010, 6: 1.035}
        dow_mult = dow_effects.get(dow, 1.0)

        # 3. Booking window lead multiplier
        lead_mult = cls.WINDOW_FARE_MULTIPLIERS.get(booking_window, 1.0)

        # 4. Booking window time-dynamics
        window_drift = {
            1: 1.0 + 0.0030 * day_offset,   # T+1: high volatility surge
            7: 1.0 + 0.0028 * day_offset,   # T+7: moderate surge
            15: 1.0 + 0.0015 * day_offset,  # T+15: baseline growth
            30: 1.0 + 0.0008 * day_offset,  # T+30: steady advance
            45: 1.0 + 0.0005 * day_offset,  # T+45: early bird saver
        }
        w_dyn = window_drift.get(booking_window, 1.0 + 0.0015 * day_offset)

        # 5. Route corridor dynamics
        route_drift = {
            ("DEL", "BOM"): 1.0 + 0.0020 * day_offset,
            ("BOM", "DEL"): 1.0 + 0.0020 * day_offset,
            ("DEL", "BLR"): 1.0 + 0.0012 * day_offset,
            ("BLR", "DEL"): 1.0 + 0.0012 * day_offset,
            ("BOM", "BLR"): 1.0 + 0.0006 * day_offset,
            ("BLR", "BOM"): 1.0 + 0.0006 * day_offset,
        }
        r_dyn = route_drift.get((origin, destination), 1.0 + 0.0014 * day_offset)

        # 6. Specific localized airfare shock on DEL-BOM during days 18-24
        shock = 1.055 if ((origin, destination) == ("DEL", "BOM") and 18 <= day_offset <= 24) else 1.0

        # 7. Airline multiplier
        air_mult = 0.96 if airline == "Akasa Air" else (1.08 if airline == "Air India" else 1.00)

        # Normalized dynamics around macro baseline
        norm_w = w_dyn / (1.0 + 0.0015 * day_offset)
        norm_r = r_dyn / (1.0 + 0.0014 * day_offset)
        raw_amt = base_price * lead_mult * air_mult * macro * norm_w * dow_mult * norm_r * shock * price_factor
        return round(raw_amt, 2)

    def collect(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        day_offset: int = 0,
    ) -> list[RawFareRecord]:
        from datetime import timezone
        observation_date = date.today()
        lead_days = (travel_date - observation_date).days
        base_price = 4800.0
        dow = travel_date.weekday()
        records = []
        now = datetime.now(timezone.utc)
        for airline, flight_num, dep_time, fare_type, _ in self.FLIGHTS:
            amt = self.calculate_deterministic_fare(
                origin=origin,
                destination=destination,
                airline=airline,
                booking_window=lead_days,
                base_price=base_price,
                day_offset=day_offset,
                dow=dow,
            )
            records.append(
                RawFareRecord(
                    origin=origin,
                    destination=destination,
                    travel_date=travel_date,
                    observation_date=observation_date,
                    booking_window=lead_days,
                    airline=airline,
                    flight_number=flight_num,
                    departure_time=dep_time,
                    cabin_class="ECONOMY",
                    fare_type=fare_type,
                    baggage_characteristics="15KG",
                    fare_amount=amt,
                    currency="INR",
                    source="mock",
                    observation_timestamp=now,
                )
            )
        return records

    def collect_basket(
        self,
        observation_date: date | None = None,
        price_factor: float = 1.0,
        source: str = "mock",
        day_offset: int = 0,
    ) -> list[RawFareRecord]:
        """Collect full representative basket across all routes and booking windows."""
        from datetime import timedelta, timezone
        obs_date = observation_date or date.today()
        dow = obs_date.weekday()
        records = []
        now = datetime.now(timezone.utc)
        for orig, dest, weight, base_price in self.DEFAULT_ROUTES:
            for lead_days in self.WINDOW_LEAD_DAYS:
                travel_date = obs_date + timedelta(days=lead_days)
                for airline, flight_num, dep_time, fare_type, _ in self.FLIGHTS:
                    amount = self.calculate_deterministic_fare(
                        origin=orig,
                        destination=dest,
                        airline=airline,
                        booking_window=lead_days,
                        base_price=base_price,
                        day_offset=day_offset,
                        dow=dow,
                        price_factor=price_factor,
                    )
                    records.append(
                        RawFareRecord(
                            origin=orig,
                            destination=dest,
                            travel_date=travel_date,
                            observation_date=obs_date,
                            booking_window=lead_days,
                            airline=airline,
                            flight_number=flight_num,
                            departure_time=dep_time,
                            cabin_class="ECONOMY",
                            fare_type=fare_type,
                            baggage_characteristics="15KG",
                            fare_amount=amount,
                            currency="INR",
                            source=source,
                            observation_timestamp=now,
                            metadata={
                                "synthetic_mode": True,
                                "window_code": f"T+{lead_days}",
                                "route_weight": weight,
                                "day_offset": day_offset,
                            },
                        )
                    )
        return records