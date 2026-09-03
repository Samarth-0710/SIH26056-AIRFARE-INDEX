"""Cross-module integration tests for the statistical-engine module.

Validates that other modules (backend, intelligence, data-quality) can consume
statistical-engine via its clean public API.
"""

from datetime import date, datetime
import unittest

from statistical_engine import (
    AirfareStatisticalEngine,
    BookingWindow,
    CalculationStatus,
    FareObservation,
    WeightConfig,
)


class TestCrossModuleConsumption(unittest.TestCase):
    """Verify clean consumer API of statistical_engine."""

    def test_consumer_pipeline(self):
        engine = AirfareStatisticalEngine()

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
                comparable_fare=5250.0,
                source="PORTAL_A",
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
                source="PORTAL_A",
                observation_timestamp=datetime(2024, 4, 7, 10, 0),
            )
        ]

        weights = WeightConfig(
            version="SHARED_TRUNK_V1",
            source="CONFIGURED",
            weights={"DEL-BOM": 1.0},
        )

        output = engine.calculate_daily_indices(
            current_observations=curr,
            previous_observations=prev,
            observation_date=date(2024, 4, 8),
            previous_observation_date=date(2024, 4, 7),
            weight_config=weights,
            target_booking_windows=[BookingWindow.T_7],
        )

        self.assertEqual(output.status, CalculationStatus.SUCCESS)
        nat_res = output.national_results[BookingWindow.T_7]
        self.assertAlmostEqual(nat_res.national_index, 105.0)
        self.assertIn("DEL-BOM", output.route_results)


if __name__ == "__main__":
    unittest.main()
