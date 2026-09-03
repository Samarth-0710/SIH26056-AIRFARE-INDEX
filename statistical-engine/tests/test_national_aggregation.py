from datetime import date, datetime
import unittest

from statistical_engine.aggregation.national_aggregator import calculate_national_index
from statistical_engine.engine import AirfareStatisticalEngine
from statistical_engine.models.index_result import (
    CalculationStatus,
    ElementaryIndexResult,
    RouteIndexResult,
)
from statistical_engine.models.observation import BookingWindow, FareObservation
from statistical_engine.models.weights import WeightConfig


class TestNationalAggregation(unittest.TestCase):
    """Test national aggregate index calculations."""

    def _make_route_result(self, route: str, bw: BookingWindow, idx_val: float):
        elem = ElementaryIndexResult(
            route=route,
            booking_window=bw,
            index_value=idx_val,
            geometric_mean_relative=idx_val / 100.0,
            num_matched_pairs=5,
            num_current_observations=10,
            num_previous_observations=10,
            status=CalculationStatus.SUCCESS,
        )
        return RouteIndexResult(
            route=route,
            window_indices={bw: elem},
            status=CalculationStatus.SUCCESS,
        )

    def test_national_aggregation_hand_calculated(self):
        # DEL-BOM: index 110.0, weight 0.6
        # BOM-BLR: index 120.0, weight 0.4
        # Expected: 0.6 * 110.0 + 0.4 * 120.0 = 66.0 + 48.0 = 114.0
        route_results = {
            "DEL-BOM": self._make_route_result("DEL-BOM", BookingWindow.T_7, 110.0),
            "BOM-BLR": self._make_route_result("BOM-BLR", BookingWindow.T_7, 120.0),
        }
        weights = WeightConfig(
            version="TEST_WEIGHTS_V1",
            source="TEST",
            weights={"DEL-BOM": 0.6, "BOM-BLR": 0.4},
        )

        res = calculate_national_index(
            route_results=route_results,
            weight_config=weights,
            booking_window=BookingWindow.T_7,
        )

        self.assertEqual(res.status, CalculationStatus.SUCCESS)
        self.assertAlmostEqual(res.national_index, 114.0)
        self.assertAlmostEqual(res.coverage_ratio, 1.0)
        self.assertEqual(res.weight_version, "TEST_WEIGHTS_V1")

    def test_default_strict_coverage_behavior(self):
        # 3 routes in basket, but DEL-BLR missing
        route_results = {
            "DEL-BOM": self._make_route_result("DEL-BOM", BookingWindow.T_7, 110.0),
            "BOM-BLR": self._make_route_result("BOM-BLR", BookingWindow.T_7, 120.0),
        }
        weights = WeightConfig(
            version="TEST_WEIGHTS_3ROUTES",
            source="TEST",
            weights={"DEL-BOM": 0.5, "BOM-BLR": 0.3, "DEL-BLR": 0.2},
        )

        # Default call (without passing allow_partial_coverage) MUST be strict (False)
        res_default = calculate_national_index(
            route_results=route_results,
            weight_config=weights,
            booking_window=BookingWindow.T_7,
        )
        self.assertEqual(res_default.status, CalculationStatus.INSUFFICIENT_DATA)
        self.assertIsNone(res_default.national_index)
        self.assertTrue(any("strict authoritative coverage" in w for w in res_default.warnings))

    def test_partial_coverage_explicit_opt_in(self):
        # 3 routes weighted in basket: DEL-BOM (0.5), BOM-BLR (0.3), DEL-BLR (0.2)
        # But DEL-BLR is missing from route results
        route_results = {
            "DEL-BOM": self._make_route_result("DEL-BOM", BookingWindow.T_7, 110.0),
            "BOM-BLR": self._make_route_result("BOM-BLR", BookingWindow.T_7, 120.0),
        }
        weights = WeightConfig(
            version="TEST_WEIGHTS_3ROUTES",
            source="TEST",
            weights={"DEL-BOM": 0.5, "BOM-BLR": 0.3, "DEL-BLR": 0.2},
        )

        # 1. When allow_partial_coverage is explicitly False -> INSUFFICIENT_DATA
        res_strict = calculate_national_index(
            route_results=route_results,
            weight_config=weights,
            booking_window=BookingWindow.T_7,
            allow_partial_coverage=False,
        )
        self.assertEqual(res_strict.status, CalculationStatus.INSUFFICIENT_DATA)
        self.assertIsNone(res_strict.national_index)

        # 2. When allow_partial_coverage is explicitly opted into (True) -> re-normalizes over observed 0.8
        # DEL-BOM re-normalized: 0.5 / 0.8 = 0.625
        # BOM-BLR re-normalized: 0.3 / 0.8 = 0.375
        # Expected: 0.625 * 110.0 + 0.375 * 120.0 = 68.75 + 45.0 = 113.75
        res_partial = calculate_national_index(
            route_results=route_results,
            weight_config=weights,
            booking_window=BookingWindow.T_7,
            allow_partial_coverage=True,
        )
        self.assertEqual(res_partial.status, CalculationStatus.PARTIAL_COVERAGE)
        self.assertAlmostEqual(res_partial.national_index, 113.75)
        self.assertAlmostEqual(res_partial.coverage_ratio, 0.8)

    def test_deterministic_calculation(self):
        route_results = {
            "DEL-BOM": self._make_route_result("DEL-BOM", BookingWindow.T_7, 105.4321),
            "BOM-BLR": self._make_route_result("BOM-BLR", BookingWindow.T_7, 98.7654),
        }
        weights = WeightConfig(
            version="TEST_DET",
            source="TEST",
            weights={"DEL-BOM": 0.7, "BOM-BLR": 0.3},
        )

        res1 = calculate_national_index(route_results, weights, BookingWindow.T_7)
        res2 = calculate_national_index(route_results, weights, BookingWindow.T_7)
        self.assertEqual(res1.national_index, res2.national_index)

    def test_engine_level_default_strict_coverage(self):
        engine = AirfareStatisticalEngine()
        self.assertFalse(engine.allow_partial_coverage)

        # Observations only provide DEL-BOM
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
                source="TEST",
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
                source="TEST",
                observation_timestamp=datetime(2024, 4, 7, 10, 0),
            )
        ]

        # Weights basket requires both DEL-BOM and BOM-BLR
        weights = WeightConfig(
            version="TEST_WEIGHTS_2ROUTES",
            source="TEST",
            weights={"DEL-BOM": 0.6, "BOM-BLR": 0.4},
        )

        # 1. Default calculation must return INSUFFICIENT_DATA because BOM-BLR is missing
        out_strict = engine.calculate_daily_indices(
            current_observations=curr,
            previous_observations=prev,
            observation_date=date(2024, 4, 8),
            previous_observation_date=date(2024, 4, 7),
            weight_config=weights,
            target_booking_windows=[BookingWindow.T_7],
        )
        self.assertEqual(out_strict.status, CalculationStatus.INSUFFICIENT_DATA)
        self.assertEqual(
            out_strict.national_results[BookingWindow.T_7].status,
            CalculationStatus.INSUFFICIENT_DATA,
        )
        self.assertIsNone(out_strict.national_results[BookingWindow.T_7].national_index)

        # 2. When explicitly opted in to allow_partial_coverage=True, it succeeds with PARTIAL_COVERAGE
        out_partial = engine.calculate_daily_indices(
            current_observations=curr,
            previous_observations=prev,
            observation_date=date(2024, 4, 8),
            previous_observation_date=date(2024, 4, 7),
            weight_config=weights,
            target_booking_windows=[BookingWindow.T_7],
            allow_partial_coverage=True,
        )
        self.assertEqual(out_partial.status, CalculationStatus.SUCCESS)
        self.assertEqual(
            out_partial.national_results[BookingWindow.T_7].status,
            CalculationStatus.PARTIAL_COVERAGE,
        )
        self.assertIsNotNone(out_partial.national_results[BookingWindow.T_7].national_index)


if __name__ == "__main__":
    unittest.main()
