"""Tests for reproducibility metadata and calculation determinism."""

from datetime import date, datetime
import json
import unittest

from statistical_engine.engine import AirfareStatisticalEngine
from statistical_engine.models.observation import BookingWindow, FareObservation
from statistical_engine.models.weights import WeightConfig


class TestReproducibility(unittest.TestCase):
    """Test deterministic output, checksum, and reproducibility metadata retention."""

    def _create_sample_observations(self):
        curr = [
            FareObservation(
                origin="DEL",
                destination="BOM",
                travel_date=date(2024, 4, 15),
                observation_date=date(2024, 4, 8),
                booking_window=BookingWindow.T_7,
                airline="6E",
                flight_number="6E-101",
                departure_time="07:00",
                cabin_class="ECONOMY",
                fare_type="SAVER",
                baggage_characteristics="15KG",
                comparable_fare=5500.0,
                source="SRC_A",
                observation_timestamp=datetime(2024, 4, 8, 10, 0),
            )
        ]
        prev = [
            FareObservation(
                origin="DEL",
                destination="BOM",
                travel_date=date(2024, 4, 15),
                observation_date=date(2024, 4, 7),
                booking_window=BookingWindow.T_7,
                airline="6E",
                flight_number="6E-101",
                departure_time="07:00",
                cabin_class="ECONOMY",
                fare_type="SAVER",
                baggage_characteristics="15KG",
                comparable_fare=5000.0,
                source="SRC_A",
                observation_timestamp=datetime(2024, 4, 7, 10, 0),
            )
        ]
        return curr, prev

    def test_reproducibility_metadata_and_determinism(self):
        engine = AirfareStatisticalEngine()
        curr, prev = self._create_sample_observations()

        weights = WeightConfig(
            version="W_TEST_V1",
            source="TEST",
            weights={"DEL-BOM": 1.0},
        )

        out1 = engine.calculate_daily_indices(
            current_observations=curr,
            previous_observations=prev,
            observation_date=date(2024, 4, 8),
            previous_observation_date=date(2024, 4, 7),
            weight_config=weights,
            observation_set_version="OBS_20240408_01",
            basket_version="BASKET_2024_01",
            target_booking_windows=[BookingWindow.T_7],
        )

        out2 = engine.calculate_daily_indices(
            current_observations=curr,
            previous_observations=prev,
            observation_date=date(2024, 4, 8),
            previous_observation_date=date(2024, 4, 7),
            weight_config=weights,
            observation_set_version="OBS_20240408_01",
            basket_version="BASKET_2024_01",
            target_booking_windows=[BookingWindow.T_7],
        )

        # Mathematical outputs must be strictly equal
        self.assertEqual(
            out1.national_results[BookingWindow.T_7].national_index,
            out2.national_results[BookingWindow.T_7].national_index,
        )
        self.assertEqual(
            out1.reproducibility.execution_checksum,
            out2.reproducibility.execution_checksum,
        )
        self.assertEqual(out1.reproducibility.observation_set_version, "OBS_20240408_01")
        self.assertEqual(out1.reproducibility.basket_version, "BASKET_2024_01")
        self.assertEqual(out1.reproducibility.weight_version, "W_TEST_V1")

        # Verify JSON serializability of complete output
        out_dict = out1.to_dict()
        json_str = json.dumps(out_dict)
        self.assertIn("DEL-BOM", json_str)
        self.assertIn("W_TEST_V1", json_str)


if __name__ == "__main__":
    unittest.main()
