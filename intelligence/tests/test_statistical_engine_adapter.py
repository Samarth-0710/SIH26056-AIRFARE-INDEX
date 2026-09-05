import unittest
from datetime import date, datetime
from unittest.mock import Mock

from intelligence.integration.statistical_engine_adapter import (
    StatisticalEngineIntelligenceAdapter,
)
from intelligence.models.result import IntelligenceOutput
from statistical_engine.models.index_result import (
    CalculationStatus,
    ElementaryIndexResult,
    EngineCalculationOutput,
    NationalIndexResult,
    ReproducibilityMetadata,
    RouteIndexResult,
)
from statistical_engine.models.observation import BookingWindow


def build_engine_output() -> EngineCalculationOutput:
    windows = {}
    for window, value in (
        (BookingWindow.T_1, 101.0),
        (BookingWindow.T_7, 108.0),
        (BookingWindow.T_15, 115.0),
    ):
        windows[window] = ElementaryIndexResult(
            route="DEL-BOM",
            booking_window=window,
            index_value=value,
            geometric_mean_relative=value / 100.0,
            num_matched_pairs=1,
            num_current_observations=1,
            num_previous_observations=1,
            status=CalculationStatus.SUCCESS,
        )

    route_result = RouteIndexResult(
        route="DEL-BOM",
        window_indices=windows,
        status=CalculationStatus.SUCCESS,
    )
    national_results = {
        window: NationalIndexResult(
            booking_window=window,
            national_index=value,
            route_indices={"DEL-BOM": value},
            route_contributions={},
            coverage_ratio=0.75,
            weight_version="TEST_WEIGHTS",
            status=CalculationStatus.SUCCESS,
        )
        for window, value in (
            (BookingWindow.T_1, 101.0),
            (BookingWindow.T_7, 108.0),
            (BookingWindow.T_15, 115.0),
        )
    }
    return EngineCalculationOutput(
        observation_date=date(2026, 9, 5),
        previous_observation_date=date(2026, 9, 4),
        route_results={"DEL-BOM": route_result},
        national_results=national_results,
        reproducibility=ReproducibilityMetadata(
            observation_set_version="TEST_OBS",
            basket_version="TEST_BASKET",
            weight_version="TEST_WEIGHTS",
            methodology_version="TEST_METHOD",
            calculation_timestamp=datetime(2026, 9, 5, 0, 0),
            execution_checksum="checksum",
        ),
        status=CalculationStatus.SUCCESS,
    )


class TestStatisticalEngineIntelligenceAdapter(unittest.TestCase):
    def setUp(self):
        self.engine_output = build_engine_output()
        self.orchestrator = Mock()
        self.orchestrator.analyze.return_value = IntelligenceOutput(
            observation_date="2026-09-05"
        )
        self.adapter = StatisticalEngineIntelligenceAdapter(self.orchestrator)

    def test_forwards_route_indices_and_coverage(self):
        result = self.adapter.analyze(self.engine_output, "T+7", {"DEL-BOM": 100.0})

        self.assertIsInstance(result, IntelligenceOutput)
        kwargs = self.orchestrator.analyze.call_args.kwargs
        self.assertEqual(kwargs["current_route_indices"], {"DEL-BOM": 108.0})
        self.assertEqual(kwargs["previous_route_indices"], {"DEL-BOM": 100.0})
        self.assertEqual(kwargs["booking_window"], "T+7")
        self.assertEqual(kwargs["coverage_ratio"], 0.75)

    def test_multiple_windows_are_mapped(self):
        results = self.adapter.analyze_windows(
            self.engine_output, ["T+1", BookingWindow.T_15]
        )

        self.assertEqual(set(results), {BookingWindow.T_1, BookingWindow.T_15})
        calls = self.orchestrator.analyze.call_args_list
        self.assertEqual([call.kwargs["booking_window"] for call in calls], ["T+1", "T+15"])

    def test_missing_window_result_is_safe_and_warned(self):
        result = self.adapter.analyze(self.engine_output, BookingWindow.T_30)

        kwargs = self.orchestrator.analyze.call_args.kwargs
        self.assertEqual(kwargs["current_route_indices"], {})
        self.assertTrue(any("No index result" in warning for warning in result.warnings))
        self.assertTrue(any("coverage is unknown" in warning for warning in result.warnings))

    def test_engine_output_is_unchanged(self):
        before = self.engine_output.to_dict()

        self.adapter.analyze(self.engine_output, BookingWindow.T_7)

        self.assertEqual(self.engine_output.to_dict(), before)

    def test_empty_route_results_are_safe(self):
        empty = build_engine_output()
        empty.route_results.clear()

        result = self.adapter.analyze(empty, BookingWindow.T_7)

        self.assertEqual(
            self.orchestrator.analyze.call_args.kwargs["current_route_indices"], {}
        )
        self.assertIsInstance(result, IntelligenceOutput)


if __name__ == "__main__":
    unittest.main()