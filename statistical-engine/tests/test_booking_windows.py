"""Tests for booking window separation and handling."""

from datetime import date, datetime
import unittest

from statistical_engine.aggregation.route_aggregator import calculate_route_indices
from statistical_engine.models.observation import BookingWindow, FareObservation


class TestBookingWindows(unittest.TestCase):
    """Test strictly separate calculation for documented booking windows."""

    def _make_obs(self, bw: BookingWindow, fare: float, is_curr: bool):
        obs_d = date(2024, 4, 8) if is_curr else date(2024, 4, 7)
        return FareObservation(
            origin="DEL",
            destination="BOM",
            travel_date=date(2024, 4, 20),
            observation_date=obs_d,
            booking_window=bw,
            airline="6E",
            flight_number="6E-101",
            departure_time="08:00",
            cabin_class="ECONOMY",
            fare_type="SAVER",
            baggage_characteristics="15KG",
            comparable_fare=fare,
            source="TEST",
            observation_timestamp=datetime(2024, 4, 8, 10, 0),
        )

    def test_separate_booking_windows_non_mixing(self):
        # T+1 price went up 20% (5000 -> 6000)
        # T+7 price stayed flat 0% (5000 -> 5000)
        # T+15 price went down 10% (5000 -> 4500)
        # T+30 price went up 10% (5000 -> 5500)
        # T+45 price stayed flat (4000 -> 4000)
        curr = [
            self._make_obs(BookingWindow.T_1, 6000.0, True),
            self._make_obs(BookingWindow.T_7, 5000.0, True),
            self._make_obs(BookingWindow.T_15, 4500.0, True),
            self._make_obs(BookingWindow.T_30, 5500.0, True),
            self._make_obs(BookingWindow.T_45, 4000.0, True),
        ]
        prev = [
            self._make_obs(BookingWindow.T_1, 5000.0, False),
            self._make_obs(BookingWindow.T_7, 5000.0, False),
            self._make_obs(BookingWindow.T_15, 5000.0, False),
            self._make_obs(BookingWindow.T_30, 5000.0, False),
            self._make_obs(BookingWindow.T_45, 4000.0, False),
        ]

        results = calculate_route_indices(curr, prev)
        r_res = results["DEL-BOM"]

        # Check each window has isolated, non-leaked index
        self.assertAlmostEqual(r_res.window_indices[BookingWindow.T_1].index_value, 120.0)
        self.assertAlmostEqual(r_res.window_indices[BookingWindow.T_7].index_value, 100.0)
        self.assertAlmostEqual(r_res.window_indices[BookingWindow.T_15].index_value, 90.0)
        self.assertAlmostEqual(r_res.window_indices[BookingWindow.T_30].index_value, 110.0)
        self.assertAlmostEqual(r_res.window_indices[BookingWindow.T_45].index_value, 100.0)

    def test_unsupported_window_rejection(self):
        with self.assertRaises(ValueError):
            BookingWindow.from_string("T+60")


if __name__ == "__main__":
    unittest.main()
