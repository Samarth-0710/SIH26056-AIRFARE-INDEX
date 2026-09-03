"""Tests for weight validation, coverage, and normalization."""

import unittest

from statistical_engine.aggregation.weights_manager import (
    calculate_weight_coverage,
    renormalize_weights_for_subbasket,
    validate_weight_config,
)
from statistical_engine.models.weights import WeightConfig, get_demo_reference_weights


class TestWeights(unittest.TestCase):
    """Test weight manager functionality."""

    def test_validate_weight_config_valid(self):
        cfg = WeightConfig(
            version="TEST_V1",
            source="TEST",
            weights={"DEL-BOM": 0.5, "BOM-BLR": 0.5},
        )
        is_valid, errors = validate_weight_config(cfg)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_weight_coverage_full_and_partial(self):
        cfg = WeightConfig(
            version="TEST_V1",
            source="TEST",
            weights={"DEL-BOM": 0.5, "BOM-BLR": 0.3, "DEL-BLR": 0.2},
        )

        # Full coverage
        cov_full, present, missing = calculate_weight_coverage(
            observed_routes={"DEL-BOM", "BOM-BLR", "DEL-BLR"},
            weight_config=cfg,
        )
        self.assertAlmostEqual(cov_full, 1.0)
        self.assertEqual(len(missing), 0)

        # Partial coverage: DEL-BLR missing
        cov_part, present, missing = calculate_weight_coverage(
            observed_routes={"DEL-BOM", "BOM-BLR"},
            weight_config=cfg,
        )
        self.assertAlmostEqual(cov_part, 0.8)
        self.assertEqual(missing, ["DEL-BLR"])

    def test_renormalize_weights_for_subbasket(self):
        cfg = WeightConfig(
            version="TEST_V1",
            source="TEST",
            weights={"DEL-BOM": 0.6, "BOM-BLR": 0.4},
        )
        # Only DEL-BOM observed
        renorm, total_sub = renormalize_weights_for_subbasket(
            available_routes={"DEL-BOM"},
            weight_config=cfg,
        )
        self.assertAlmostEqual(total_sub, 0.6)
        self.assertAlmostEqual(renorm["DEL-BOM"], 1.0)

    def test_auto_normalize_factory(self):
        # Raw weights sum to 200
        cfg = WeightConfig.from_raw_weights(
            raw_weights={"DEL-BOM": 150.0, "BOM-BLR": 50.0},
            version="AUTO_NORM_V1",
            auto_normalize=True,
        )
        self.assertAlmostEqual(cfg.get_weight("DEL-BOM"), 0.75)
        self.assertAlmostEqual(cfg.get_weight("BOM-BLR"), 0.25)


if __name__ == "__main__":
    unittest.main()
