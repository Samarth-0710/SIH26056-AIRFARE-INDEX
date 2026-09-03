"""End-to-end integration tests for the statistical index engine."""

from datetime import date, datetime
import unittest

from statistical_engine.engine import AirfareStatisticalEngine
from statistical_engine.models.index_result import CalculationStatus
from statistical_engine.models.observation import BookingWindow, FareObservation
from statistical_engine.models.weights import WeightConfig


class TestEndToEndEngine(unittest.TestCase):
    """Test complete end-to-end statistical engine calculation pipeline."""

    def _build_mock_dataset(self):
        curr_obs = []
        prev_obs = []

        routes = ["DEL-BOM", "BOM-BLR", "DEL-BLR"]
        windows = [
            BookingWindow.T_1,
            BookingWindow.T_7,
            BookingWindow.T_15,
            BookingWindow.T_30,
            BookingWindow.T_45,
        ]

        # Route-specific base fares and movement factors
        factors = {
            "DEL-BOM": 1.10,  # +10%
            "BOM-BLR": 0.95,  # -5%
            "DEL-BLR": 1.05,  # +5%
        }
        base_fares = {
            "DEL-BOM": 5000.0,
            "BOM-BLR": 4000.0,
            "DEL-BLR": 6000.0,
        }

        for route in routes:
            orig, dest = route.split("-")
            for bw in windows:
                for fl_idx in [101, 102]:
                    flight_num = f"6E-{fl_idx}"
                    p_fare = base_fares[route] + (fl_idx - 100) * 200.0
                    c_fare = p_fare * factors[route]

                    # t-1 observation
                    prev_obs.append(
                        FareObservation(
                            origin=orig,
                            destination=dest,
                            travel_date=date(2024, 4, 20),
                            observation_date=date(2024, 4, 7),
                            booking_window=bw,
                            airline="6E",
                            flight_number=flight_num,
                            departure_time="08:00",
                            cabin_class="ECONOMY",
                            fare_type="SAVER",
                            baggage_characteristics="15KG",
                            comparable_fare=p_fare,
                            source="TEST_FEED",
                            observation_timestamp=datetime(2024, 4, 7, 10, 0),
                        )
                    )

                    # t observation
                    curr_obs.append(
                        FareObservation(
                            origin=orig,
                            destination=dest,
                            travel_date=date(2024, 4, 20),
                            observation_date=date(2024, 4, 8),
                            booking_window=bw,
                            airline="6E",
                            flight_number=flight_num,
                            departure_time="08:00",
                            cabin_class="ECONOMY",
                            fare_type="SAVER",
                            baggage_characteristics="15KG",
                            comparable_fare=c_fare,
                            source="TEST_FEED",
                            observation_timestamp=datetime(2024, 4, 8, 10, 0),
                        )
                    )

        return curr_obs, prev_obs

    def test_full_pipeline_multi_route_multi_window(self):
        curr_obs, prev_obs = self._build_mock_dataset()

        # Configured route weights
        # DEL-BOM: 0.5, BOM-BLR: 0.3, DEL-BLR: 0.2
        weights = WeightConfig(
            version="TEST_WEIGHTS_INDIA_TRUNK",
            source="TEST_DERIVED",
            weights={"DEL-BOM": 0.5, "BOM-BLR": 0.3, "DEL-BLR": 0.2},
            description="Test trunk route weights for validation",
        )

        engine = AirfareStatisticalEngine()

        # Pass t-1 base indices (all 100.0) to test point change & contributions
        prev_route_indices = {
            bw: {"DEL-BOM": 100.0, "BOM-BLR": 100.0, "DEL-BLR": 100.0}
            for bw in BookingWindow
        }

        output = engine.calculate_daily_indices(
            current_observations=curr_obs,
            previous_observations=prev_obs,
            observation_date=date(2024, 4, 8),
            previous_observation_date=date(2024, 4, 7),
            weight_config=weights,
            observation_set_version="OBS_TRUNK_20240408",
            basket_version="BASKET_TRUNK_V1",
            previous_route_indices=prev_route_indices,
        )

        self.assertEqual(output.status, CalculationStatus.SUCCESS)
        self.assertEqual(len(output.route_results), 3)
        self.assertEqual(len(output.national_results), 5)

        # Expected route indices:
        # DEL-BOM: 110.0
        # BOM-BLR: 95.0
        # DEL-BLR: 105.0
        del_bom_t7 = output.route_results["DEL-BOM"].window_indices[BookingWindow.T_7]
        self.assertAlmostEqual(del_bom_t7.index_value, 110.0)

        bom_blr_t7 = output.route_results["BOM-BLR"].window_indices[BookingWindow.T_7]
        self.assertAlmostEqual(bom_blr_t7.index_value, 95.0)

        del_blr_t7 = output.route_results["DEL-BLR"].window_indices[BookingWindow.T_7]
        self.assertAlmostEqual(del_blr_t7.index_value, 105.0)

        # Expected National Index:
        # 0.5 * 110.0 + 0.3 * 95.0 + 0.2 * 105.0 = 55.0 + 28.5 + 21.0 = 104.5
        nat_t7 = output.national_results[BookingWindow.T_7]
        self.assertEqual(nat_t7.status, CalculationStatus.SUCCESS)
        self.assertAlmostEqual(nat_t7.national_index, 104.5)
        self.assertAlmostEqual(nat_t7.coverage_ratio, 1.0)

        # Point contributions to change (from base 100.0 to 104.5 -> Delta = +4.5)
        # DEL-BOM: 0.5 * (110 - 100) = +5.0
        # BOM-BLR: 0.3 * (95 - 100) = -1.5
        # DEL-BLR: 0.2 * (105 - 100) = +1.0
        # Sum = 5.0 - 1.5 + 1.0 = +4.5
        contribs = nat_t7.route_contributions
        self.assertAlmostEqual(contribs["DEL-BOM"].point_contribution, 5.0)
        self.assertAlmostEqual(contribs["BOM-BLR"].point_contribution, -1.5)
        self.assertAlmostEqual(contribs["DEL-BLR"].point_contribution, 1.0)

        total_point_contrib = sum(c.point_contribution for c in contribs.values())
        self.assertAlmostEqual(total_point_contrib, 4.5)

        # Percentage shares:
        # DEL-BOM: 5.0 / 4.5 = 111.111%
        # BOM-BLR: -1.5 / 4.5 = -33.333%
        # DEL-BLR: 1.0 / 4.5 = 22.222%
        # Sum = 100%
        total_pct_share = sum(c.percentage_share_of_change for c in contribs.values())
        self.assertAlmostEqual(total_pct_share, 100.0)

        # Check reproducibility metadata
        self.assertEqual(output.reproducibility.basket_version, "BASKET_TRUNK_V1")
        self.assertEqual(output.reproducibility.weight_version, "TEST_WEIGHTS_INDIA_TRUNK")
        self.assertTrue(len(output.reproducibility.execution_checksum) > 0)


if __name__ == "__main__":
    unittest.main()
