"""Tests for comparability matching and fingerprinting."""

from datetime import date, datetime
import unittest

from statistical_engine.core.comparability import (
    generate_fare_fingerprint,
    match_comparable_pairs,
)
from statistical_engine.models.observation import (
    BookingWindow,
    FareObservation,
    QualityStatus,
)


class TestComparability(unittest.TestCase):
    """Test fare fingerprinting and pair matching."""

    def _make_obs(
        self,
        origin="DEL",
        dest="BOM",
        travel_d=date(2024, 4, 15),
        obs_d=date(2024, 4, 8),
        bw=BookingWindow.T_7,
        airline="6E",
        flight_num="6E-201",
        dep_time="07:00",
        fare=5000.0,
        status=QualityStatus.VALID,
    ):
        return FareObservation(
            origin=origin,
            destination=dest,
            travel_date=travel_d,
            observation_date=obs_d,
            booking_window=bw,
            airline=airline,
            flight_number=flight_num,
            departure_time=dep_time,
            cabin_class="ECONOMY",
            fare_type="SAVER",
            baggage_characteristics="15KG",
            comparable_fare=fare,
            source="TEST",
            observation_timestamp=datetime(2024, 4, 8, 12, 0),
            quality_status=status,
        )

    def test_fingerprint_deterministic_and_unique(self):
        obs1 = self._make_obs(fare=5000.0)
        obs2 = self._make_obs(fare=6000.0)  # Fare difference should NOT change comparability fingerprint
        obs3 = self._make_obs(flight_num="6E-202")  # Different flight

        fp1 = generate_fare_fingerprint(obs1)
        fp2 = generate_fare_fingerprint(obs2)
        fp3 = generate_fare_fingerprint(obs3)

        self.assertEqual(fp1, fp2)
        self.assertNotEqual(fp1, fp3)

    def test_match_comparable_pairs_normal(self):
        curr_obs = [
            self._make_obs(flight_num="6E-201", fare=5500.0),
            self._make_obs(flight_num="6E-202", fare=6200.0),
        ]
        prev_obs = [
            self._make_obs(flight_num="6E-201", fare=5000.0),
            self._make_obs(flight_num="6E-202", fare=6000.0),
        ]

        res = match_comparable_pairs(curr_obs, prev_obs)
        self.assertEqual(len(res.matched_pairs), 2)
        self.assertEqual(res.unmatched_current_count, 0)
        self.assertEqual(res.unmatched_previous_count, 0)

        # Check calculated price relatives
        rel_201 = [p for p in res.matched_pairs if p.current_observation.flight_number == "6E-201"][0]
        self.assertAlmostEqual(rel_201.price_relative, 5500.0 / 5000.0)

    def test_unmatched_and_empty_pairs(self):
        # Current has flight 201, prev has flight 202 -> zero pairs
        curr_obs = [self._make_obs(flight_num="6E-201", fare=5500.0)]
        prev_obs = [self._make_obs(flight_num="6E-202", fare=5000.0)]

        res = match_comparable_pairs(curr_obs, prev_obs)
        self.assertEqual(len(res.matched_pairs), 0)
        self.assertEqual(res.unmatched_current_count, 1)
        self.assertEqual(res.unmatched_previous_count, 1)

    def test_duplicate_handling_within_period(self):
        # Two records with exact same comparability dimensions in current period
        curr_obs = [
            self._make_obs(flight_num="6E-201", fare=5200.0),
            self._make_obs(flight_num="6E-201", fare=5000.0),  # Duplicate
        ]
        prev_obs = [
            self._make_obs(flight_num="6E-201", fare=4800.0),
        ]

        res = match_comparable_pairs(curr_obs, prev_obs)
        self.assertEqual(len(res.matched_pairs), 1)
        self.assertEqual(len(res.duplicate_fingerprints), 1)
        # Deterministic choice: picks lowest fare (5000.0)
        self.assertEqual(res.matched_pairs[0].current_observation.comparable_fare, 5000.0)

    def test_excluded_quality_status_filtered(self):
        curr_obs = [self._make_obs(flight_num="6E-201", fare=5500.0, status=QualityStatus.EXCLUDED)]
        prev_obs = [self._make_obs(flight_num="6E-201", fare=5000.0)]

        res = match_comparable_pairs(curr_obs, prev_obs)
        self.assertEqual(len(res.matched_pairs), 0)


if __name__ == "__main__":
    unittest.main()
