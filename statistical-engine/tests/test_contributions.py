"""Tests for route contribution calculations."""

import unittest

from statistical_engine.aggregation.contributions import calculate_route_contributions
from statistical_engine.models.observation import BookingWindow


class TestContributions(unittest.TestCase):
    """Test route contribution mathematics."""

    def test_level_and_point_contributions_hand_calculated(self):
        # Current indices: DEL-BOM: 110.0, BOM-BLR: 95.0
        # Previous indices: DEL-BOM: 100.0, BOM-BLR: 100.0
        # Weights: DEL-BOM: 0.6, BOM-BLR: 0.4
        curr_indices = {"DEL-BOM": 110.0, "BOM-BLR": 95.0}
        prev_indices = {"DEL-BOM": 100.0, "BOM-BLR": 100.0}
        weights = {"DEL-BOM": 0.6, "BOM-BLR": 0.4}

        # National curr = 0.6 * 110 + 0.4 * 95 = 66.0 + 38.0 = 104.0
        # National prev = 0.6 * 100 + 0.4 * 100 = 100.0
        # Total change = +4.0 points
        contribs = calculate_route_contributions(
            route_indices=curr_indices,
            weights=weights,
            booking_window=BookingWindow.T_7,
            previous_route_indices=prev_indices,
        )

        del_bom = contribs["DEL-BOM"]
        bom_blr = contribs["BOM-BLR"]

        # Level contributions
        self.assertAlmostEqual(del_bom.level_contribution, 66.0)
        self.assertAlmostEqual(bom_blr.level_contribution, 38.0)
        self.assertAlmostEqual(
            del_bom.level_contribution + bom_blr.level_contribution, 104.0
        )

        # Point contributions
        # DEL-BOM: 0.6 * (110 - 100) = +6.0
        # BOM-BLR: 0.4 * (95 - 100) = -2.0
        self.assertAlmostEqual(del_bom.point_contribution, 6.0)
        self.assertAlmostEqual(bom_blr.point_contribution, -2.0)
        self.assertAlmostEqual(
            del_bom.point_contribution + bom_blr.point_contribution, 4.0
        )

        # Percentage shares
        # DEL-BOM: 6.0 / 4.0 * 100 = 150%
        # BOM-BLR: -2.0 / 4.0 * 100 = -50%
        self.assertAlmostEqual(del_bom.percentage_share_of_change, 150.0)
        self.assertAlmostEqual(bom_blr.percentage_share_of_change, -50.0)

    def test_contributions_without_previous_indices(self):
        curr_indices = {"DEL-BOM": 110.0}
        weights = {"DEL-BOM": 1.0}

        contribs = calculate_route_contributions(
            route_indices=curr_indices,
            weights=weights,
            booking_window=BookingWindow.T_7,
            previous_route_indices=None,
        )

        del_bom = contribs["DEL-BOM"]
        self.assertAlmostEqual(del_bom.level_contribution, 110.0)
        self.assertIsNone(del_bom.point_contribution)
        self.assertIsNone(del_bom.percentage_share_of_change)


if __name__ == "__main__":
    unittest.main()
