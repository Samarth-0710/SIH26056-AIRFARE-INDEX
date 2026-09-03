"""Tests for route-level elementary index calculations."""

from datetime import date, datetime
import unittest

from statistical_engine.aggregation.route_aggregator import calculate_route_indices
from statistical_engine.models.index_result import CalculationStatus
from statistical_engine.models.observation import BookingWindow, FareObservation


class TestRouteIndex(unittest.TestCase):
    """Test route-level calculations across single and multiple routes."""

    def _make_obs(self, route: str, bw: BookingWindow, flight: str, fare: float, is_curr: bool):
        origin, dest = route.split("-")
        obs_d = date(2024, 4, 8) if is_curr else date(2024, 4, 7)
        tr_d = date(2024, 4, 15)
        return FareObservation(
            origin=origin,
            destination=dest,
            travel_date=tr_d,
            observation_date=obs_d,
            booking_window=bw,
            airline="6E",
            flight_number=flight,
            departure_time="08:00",
            cabin_class="ECONOMY",
            fare_type="SAVER",
            baggage_characteristics="15KG",
            comparable_fare=fare,
            source="TEST",
            observation_timestamp=datetime(2024, 4, 8, 10, 0),
        )

    def test_single_route_calculation(self):
        curr = [self._make_obs("DEL-BOM", BookingWindow.T_7, "6E-101", 5500.0, True)]
        prev = [self._make_obs("DEL-BOM", BookingWindow.T_7, "6E-101", 5000.0, False)]

        results = calculate_route_indices(curr, prev, target_booking_windows=[BookingWindow.T_7])
        self.assertIn("DEL-BOM", results)
        r_res = results["DEL-BOM"]
        self.assertEqual(r_res.status, CalculationStatus.SUCCESS)

        elem_t7 = r_res.window_indices[BookingWindow.T_7]
        self.assertEqual(elem_t7.status, CalculationStatus.SUCCESS)
        self.assertAlmostEqual(elem_t7.index_value, 110.0)

    def test_multiple_configurable_routes(self):
        # DEL-BOM, BOM-BLR, and a non-standard route GAU-IXB
        curr = [
            self._make_obs("DEL-BOM", BookingWindow.T_7, "6E-101", 5500.0, True),
            self._make_obs("BOM-BLR", BookingWindow.T_7, "6E-201", 4400.0, True),
            self._make_obs("GAU-IXB", BookingWindow.T_7, "6E-301", 3300.0, True),
        ]
        prev = [
            self._make_obs("DEL-BOM", BookingWindow.T_7, "6E-101", 5000.0, False),
            self._make_obs("BOM-BLR", BookingWindow.T_7, "6E-201", 4000.0, False),
            self._make_obs("GAU-IXB", BookingWindow.T_7, "6E-301", 3000.0, False),
        ]

        results = calculate_route_indices(curr, prev, target_booking_windows=[BookingWindow.T_7])
        self.assertEqual(set(results.keys()), {"DEL-BOM", "BOM-BLR", "GAU-IXB"})
        for r_name, r_res in results.items():
            self.assertEqual(r_res.status, CalculationStatus.SUCCESS)
            self.assertAlmostEqual(r_res.window_indices[BookingWindow.T_7].index_value, 110.0)

    def test_insufficient_route_data(self):
        # Route present in current, but no matching flight in previous
        curr = [self._make_obs("DEL-BOM", BookingWindow.T_7, "6E-101", 5500.0, True)]
        prev = [self._make_obs("DEL-BOM", BookingWindow.T_7, "6E-999", 5000.0, False)]

        results = calculate_route_indices(curr, prev, target_booking_windows=[BookingWindow.T_7])
        r_res = results["DEL-BOM"]
        self.assertEqual(r_res.status, CalculationStatus.INSUFFICIENT_DATA)
        self.assertIsNone(r_res.window_indices[BookingWindow.T_7].index_value)


if __name__ == "__main__":
    unittest.main()
