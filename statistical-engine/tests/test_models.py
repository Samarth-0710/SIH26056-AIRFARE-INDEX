"""Tests for statistical_engine data models."""

from datetime import date, datetime
import unittest

from statistical_engine.models.observation import (
    BookingWindow,
    FareObservation,
    QualityStatus,
)
from statistical_engine.models.weights import (
    RouteWeight,
    WeightConfig,
    WeightSource,
    get_demo_reference_weights,
)


class TestObservationModels(unittest.TestCase):
    """Test observation model validation and conversions."""

    def test_booking_window_parsing(self):
        self.assertEqual(BookingWindow.from_string("T+1"), BookingWindow.T_1)
        self.assertEqual(BookingWindow.from_string("t+7"), BookingWindow.T_7)
        self.assertEqual(BookingWindow.from_string("T_15"), BookingWindow.T_15)
        self.assertEqual(BookingWindow.from_string("T+30"), BookingWindow.T_30)
        self.assertEqual(BookingWindow.from_string("T+45"), BookingWindow.T_45)

        with self.assertRaises(ValueError):
            BookingWindow.from_string("T+10")

        with self.assertRaises(ValueError):
            BookingWindow.from_string("RANDOM")

    def test_booking_window_from_lead_days(self):
        self.assertEqual(BookingWindow.from_lead_days(1), BookingWindow.T_1)
        self.assertEqual(BookingWindow.from_lead_days(7), BookingWindow.T_7)
        self.assertEqual(BookingWindow.from_lead_days(15), BookingWindow.T_15)
        self.assertEqual(BookingWindow.from_lead_days(30), BookingWindow.T_30)
        self.assertEqual(BookingWindow.from_lead_days(45), BookingWindow.T_45)

        with self.assertRaises(ValueError):
            BookingWindow.from_lead_days(10)

    def test_valid_fare_observation(self):
        obs = FareObservation(
            origin="del",
            destination="bom",
            travel_date=date(2024, 4, 15),
            observation_date=date(2024, 4, 8),
            booking_window=BookingWindow.T_7,
            airline="6e",
            flight_number="6e-201",
            departure_time="07:00",
            cabin_class="economy",
            fare_type="saver",
            baggage_characteristics="15kg",
            comparable_fare=4500.0,
            source="TEST_SOURCE",
            observation_timestamp=datetime(2024, 4, 8, 10, 0),
        )
        self.assertEqual(obs.origin, "DEL")
        self.assertEqual(obs.destination, "BOM")
        self.assertEqual(obs.route, "DEL-BOM")
        self.assertEqual(obs.lead_days, 7)
        self.assertEqual(obs.comparable_fare, 4500.0)

        # Test dictionary roundtrip
        d = obs.to_dict()
        obs2 = FareObservation.from_dict(d)
        self.assertEqual(obs.route, obs2.route)
        self.assertEqual(obs.comparable_fare, obs2.comparable_fare)

    def test_fare_observation_invalid_fares(self):
        base_kwargs = {
            "origin": "DEL",
            "destination": "BOM",
            "travel_date": date(2024, 4, 15),
            "observation_date": date(2024, 4, 8),
            "booking_window": BookingWindow.T_7,
            "airline": "6E",
            "flight_number": "6E-201",
            "departure_time": "07:00",
            "cabin_class": "ECONOMY",
            "fare_type": "SAVER",
            "baggage_characteristics": "15KG",
            "source": "TEST",
            "observation_timestamp": datetime(2024, 4, 8, 10, 0),
        }

        # Zero fare
        with self.assertRaises(ValueError):
            FareObservation(**base_kwargs, comparable_fare=0.0)

        # Negative fare
        with self.assertRaises(ValueError):
            FareObservation(**base_kwargs, comparable_fare=-100.0)

        # NaN fare
        with self.assertRaises(ValueError):
            FareObservation(**base_kwargs, comparable_fare=float("nan"))

        # Inf fare
        with self.assertRaises(ValueError):
            FareObservation(**base_kwargs, comparable_fare=float("inf"))

    def test_fare_observation_invalid_dates_and_airports(self):
        base_kwargs = {
            "travel_date": date(2024, 4, 8),
            "observation_date": date(2024, 4, 15),  # travel before observation
            "booking_window": BookingWindow.T_7,
            "airline": "6E",
            "flight_number": "6E-201",
            "departure_time": "07:00",
            "cabin_class": "ECONOMY",
            "fare_type": "SAVER",
            "baggage_characteristics": "15KG",
            "comparable_fare": 5000.0,
            "source": "TEST",
            "observation_timestamp": datetime(2024, 4, 8, 10, 0),
        }

        # Travel date before observation date
        with self.assertRaises(ValueError):
            FareObservation(origin="DEL", destination="BOM", **base_kwargs)

        # Identical origin and destination
        base_kwargs["observation_date"] = date(2024, 4, 1)
        with self.assertRaises(ValueError):
            FareObservation(origin="DEL", destination="DEL", **base_kwargs)

        # Empty origin
        with self.assertRaises(ValueError):
            FareObservation(origin="", destination="BOM", **base_kwargs)


class TestWeightsModels(unittest.TestCase):
    """Test route weight validation and normalization."""

    def test_valid_weights(self):
        cfg = WeightConfig(
            version="TEST_V1",
            source="TEST",
            weights={"DEL-BOM": 0.6, "BOM-BLR": 0.4},
        )
        self.assertEqual(cfg.get_weight("DEL-BOM"), 0.6)
        self.assertEqual(cfg.get_weight("BOM-BLR"), 0.4)
        self.assertEqual(cfg.get_weight("UNKNOWN"), 0.0)

    def test_percentage_weights_auto_conversion(self):
        # When user passes 60.0 and 40.0, it should scale to 0.6 and 0.4
        cfg = WeightConfig(
            version="TEST_PCT",
            source="TEST",
            weights={"DEL-BOM": 60.0, "BOM-BLR": 40.0},
        )
        self.assertAlmostEqual(cfg.get_weight("DEL-BOM"), 0.6)
        self.assertAlmostEqual(cfg.get_weight("BOM-BLR"), 0.4)

    def test_weights_sum_validation(self):
        with self.assertRaises(ValueError):
            WeightConfig(
                version="TEST_BAD_SUM",
                source="TEST",
                weights={"DEL-BOM": 0.3, "BOM-BLR": 0.3},  # Sum = 0.6
            )

    def test_negative_weight_rejection(self):
        with self.assertRaises(ValueError):
            WeightConfig(
                version="TEST_NEG",
                source="TEST",
                weights={"DEL-BOM": 1.2, "BOM-BLR": -0.2},
            )

    def test_demo_weights_fixture(self):
        demo = get_demo_reference_weights()
        self.assertFalse(demo.is_official)
        self.assertEqual(demo.source, WeightSource.DEMO_FIXTURE.value)
        self.assertAlmostEqual(sum(demo.weights.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
