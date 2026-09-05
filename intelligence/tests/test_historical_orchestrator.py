import unittest
from datetime import date, datetime, timedelta
from unittest.mock import Mock

from intelligence.integration.historical_orchestrator import (
    HistoricalCalculationOrchestrator,
)
from intelligence.models.result import IntelligenceOutput
from statistical_engine.engine import AirfareStatisticalEngine
from statistical_engine.models.observation import BookingWindow, FareObservation
from statistical_engine.models.weights import WeightConfig
from statistical_engine.validation.backtest import (
    BacktestRunner,
    generate_demo_test_reference_series,
)


def observations_for(day: date, fare: float = 100.0):
    return [
        FareObservation(
            origin="DEL",
            destination="BOM",
            travel_date=day + timedelta(days=7),
            observation_date=day,
            booking_window=BookingWindow.T_7,
            airline="6E",
            flight_number="6E-101",
            departure_time="08:00",
            cabin_class="ECONOMY",
            fare_type="SAVER",
            baggage_characteristics="15KG",
            comparable_fare=fare,
            source="TEST_FIXTURE",
            observation_timestamp=datetime.combine(day, datetime.min.time()),
        )
    ]


def weights():
    return WeightConfig(
        version="TEST_WEIGHTS",
        source="TEST_FIXTURE",
        weights={"DEL-BOM": 1.0},
    )


class TestHistoricalCalculationOrchestrator(unittest.TestCase):
    def test_empty_and_one_day_sequences_have_no_fabricated_calculation(self):
        orchestrator = HistoricalCalculationOrchestrator()
        empty = orchestrator.process({})
        one_day = orchestrator.process({date(2026, 1, 1): observations_for(date(2026, 1, 1))})

        self.assertEqual(empty.daily_results, ())
        self.assertEqual(one_day.daily_results, ())
        self.assertEqual(one_day.calculated_series_by_window[BookingWindow.T_7], {})

    def test_multiple_days_create_chronological_series(self):
        start = date(2026, 1, 1)
        batches = {
            start + timedelta(days=i): observations_for(start + timedelta(days=i), 100.0 + i)
            for i in range(3)
        }
        result = HistoricalCalculationOrchestrator().process(batches, weights())

        self.assertEqual(
            [day.observation_date for day in result.daily_results],
            [date(2026, 1, 2), date(2026, 1, 3)],
        )
        self.assertEqual(list(result.calculated_series_by_window[BookingWindow.T_7]), [
            date(2026, 1, 2), date(2026, 1, 3)
        ])

    def test_exactly_thirty_calendar_days_preserves_range(self):
        start = date(2026, 2, 1)
        batches = {
            start + timedelta(days=i): observations_for(start + timedelta(days=i), 100.0 + i)
            for i in range(30)
        }
        result = HistoricalCalculationOrchestrator().process(batches, weights())

        self.assertEqual(len(result.input_dates), 30)
        self.assertEqual(len(result.daily_results), 29)
        self.assertEqual(len(result.calculated_series_by_window[BookingWindow.T_7]), 29)

    def test_multiple_windows_are_separated(self):
        start = date(2026, 3, 1)
        batches = {
            start: observations_for(start),
            start + timedelta(days=1): observations_for(start + timedelta(days=1), 110.0),
        }
        result = HistoricalCalculationOrchestrator().process(
            batches, weights(), booking_windows=[BookingWindow.T_7]
        )

        self.assertEqual(set(result.calculated_series_by_window), {BookingWindow.T_7})
        self.assertNotIn(BookingWindow.T_1, result.calculated_series_by_window)

    def test_missing_day_resets_transition_without_fabrication(self):
        start = date(2026, 4, 1)
        batches = {
            start: observations_for(start),
            start + timedelta(days=2): observations_for(start + timedelta(days=2), 110.0),
        }
        result = HistoricalCalculationOrchestrator().process(batches, weights())

        self.assertEqual(result.daily_results, ())
        self.assertEqual(result.calculated_series_by_window[BookingWindow.T_7], {})
        self.assertTrue(any("Missing historical dates" in warning for warning in result.warnings))

    def test_missing_route_result_is_not_added_to_series(self):
        start = date(2026, 4, 10)
        batches = {
            start: observations_for(start),
            start + timedelta(days=1): [],
        }
        result = HistoricalCalculationOrchestrator().process(batches, weights())

        self.assertEqual(len(result.daily_results), 1)
        self.assertEqual(result.calculated_series_by_window[BookingWindow.T_7], {})

    def test_non_date_input_is_rejected(self):
        with self.assertRaises(ValueError):
            HistoricalCalculationOrchestrator().process({"2026-01-01": []})

    def test_previous_route_indices_and_intelligence_are_forwarded_without_future_leakage(self):
        start = date(2026, 5, 1)
        batches = {
            start + timedelta(days=i): observations_for(start + timedelta(days=i), 100.0 + i)
            for i in range(4)
        }
        adapter = Mock()
        adapter.analyze.return_value = IntelligenceOutput(observation_date="test")
        result = HistoricalCalculationOrchestrator(
            intelligence_adapter=adapter
        ).process(batches, weights(), booking_windows=[BookingWindow.T_7])

        self.assertEqual(adapter.analyze.call_count, 2)
        first_call = adapter.analyze.call_args_list[0].kwargs
        self.assertEqual(first_call["previous_route_indices"], {"DEL-BOM": 101.0})
        self.assertEqual(first_call["engine_output"], result.daily_results[1].engine_output)
        self.assertEqual(result.daily_results[0].intelligence_by_window, {})

    def test_engine_outputs_are_preserved_and_backtest_shape_is_compatible(self):
        start = date(2026, 6, 1)
        batches = {
            start + timedelta(days=i): observations_for(start + timedelta(days=i), 100.0 + i)
            for i in range(2)
        }
        result = HistoricalCalculationOrchestrator().process(batches, weights())

        self.assertIs(result.engine_outputs[0], result.daily_results[0].engine_output)
        self.assertIsInstance(result.calculated_series_by_window, dict)
        self.assertIsInstance(result.calculated_series_by_window[BookingWindow.T_7], dict)
        self.assertEqual(list(result.calculated_series_by_window[BookingWindow.T_7]), [date(2026, 6, 2)])

    def test_calculated_series_is_accepted_by_existing_backtest_runner(self):
        start = date(2026, 7, 1)
        batches = {
            start + timedelta(days=i): observations_for(start + timedelta(days=i), 100.0 + i)
            for i in range(2)
        }
        result = HistoricalCalculationOrchestrator().process(batches, weights())
        reference = generate_demo_test_reference_series(start_date=start, days=2)
        backtest = BacktestRunner(
            reference_series_by_window=reference,
            reference_source_name="TEST_SYNTHETIC_ONLY",
        )

        validation = backtest.evaluate_window(
            result.calculated_series_by_window,
            start_date=start,
            end_date=start + timedelta(days=1),
        )

        self.assertEqual(validation.expected_days, 2)
        self.assertEqual(validation.reference_source, "TEST_SYNTHETIC_ONLY")


if __name__ == "__main__":
    unittest.main()