import unittest
from datetime import date, datetime, timedelta

from intelligence.integration.historical_orchestrator import (
    HistoricalCalculationOrchestrator,
)
from statistical_engine.models.observation import BookingWindow, FareObservation
from statistical_engine.models.validation_result import MetricStatus
from statistical_engine.models.weights import WeightConfig
from statistical_engine.validation.backtest import BacktestRunner


SYNTHETIC_OBSERVATION_VERSION = "synthetic-observations-v1"
SYNTHETIC_REFERENCE_VERSION = "synthetic-reference-v1"
SYNTHETIC_START_DATE = date(2026, 8, 1)
SYNTHETIC_DAYS = 30


def synthetic_weights() -> WeightConfig:
    return WeightConfig(
        version="synthetic-test-weights-v1",
        source="SYNTHETIC_TEST_FIXTURE",
        weights={"SYN-AAA": 1.0},
        description="Synthetic integration-test route weight; not official.",
        is_official=False,
    )


def synthetic_observations_for(observation_date: date, day_number: int):
    observations = []
    lead_days = {
        BookingWindow.T_1: 1,
        BookingWindow.T_7: 7,
        BookingWindow.T_15: 15,
        BookingWindow.T_30: 30,
        BookingWindow.T_45: 45,
    }

    for window_index, (window, lead_day) in enumerate(lead_days.items()):
        observations.append(
            FareObservation(
                origin="SYN",
                destination="AAA",
                travel_date=observation_date + timedelta(days=lead_day),
                observation_date=observation_date,
                booking_window=window,
                airline="SYNTHETIC",
                flight_number=f"SYN-{window_index + 1:03d}",
                departure_time="08:00",
                cabin_class="ECONOMY",
                fare_type="SYNTHETIC-SAVER",
                baggage_characteristics="SYNTHETIC-15KG",
                comparable_fare=100.0 + (window_index * 10.0) + day_number,
                source="SYNTHETIC_TEST_FIXTURE",
                observation_timestamp=datetime.combine(
                    observation_date, datetime.min.time()
                ),
                metadata={
                    "fixture_version": SYNTHETIC_OBSERVATION_VERSION,
                    "not_real_airfare": True,
                },
            )
        )
    return observations


def synthetic_observation_batches():
    return {
        SYNTHETIC_START_DATE + timedelta(days=day_number): synthetic_observations_for(
            SYNTHETIC_START_DATE + timedelta(days=day_number), day_number
        )
        for day_number in range(SYNTHETIC_DAYS)
    }


def synthetic_reference_series():
    """Create deterministic test-only reference values, not real benchmark data."""
    return {
        window: {
            SYNTHETIC_START_DATE + timedelta(days=day_number): 200.0
            + (window_index * 3.0)
            + day_number * 0.25
            for day_number in range(SYNTHETIC_DAYS)
        }
        for window_index, window in enumerate(BookingWindow)
    }


class TestSynthetic30DayBacktestIntegration(unittest.TestCase):
    def test_full_synthetic_30_day_pipeline(self):
        result = HistoricalCalculationOrchestrator().process(
            synthetic_observation_batches(),
            weight_config=synthetic_weights(),
            observation_set_version_prefix=SYNTHETIC_OBSERVATION_VERSION,
        )

        self.assertEqual(len(result.input_dates), SYNTHETIC_DAYS)
        self.assertEqual(len(result.daily_results), SYNTHETIC_DAYS - 1)
        self.assertEqual(
            result.daily_results[0].previous_observation_date,
            SYNTHETIC_START_DATE,
        )
        self.assertEqual(
            result.daily_results[-1].observation_date,
            SYNTHETIC_START_DATE + timedelta(days=SYNTHETIC_DAYS - 1),
        )
        self.assertEqual(set(result.calculated_series_by_window), set(BookingWindow))

        for window in BookingWindow:
            calculated = result.calculated_series_by_window[window]
            self.assertEqual(len(calculated), SYNTHETIC_DAYS - 1)
            self.assertEqual(list(calculated), sorted(calculated))
            self.assertNotIn(SYNTHETIC_START_DATE, calculated)

        # Intelligence begins only after a prior completed engine transition exists.
        self.assertEqual(result.daily_results[0].intelligence_by_window, {})
        self.assertTrue(result.daily_results[1].intelligence_by_window)

    def test_existing_backtest_runner_accepts_full_pipeline_output(self):
        result = HistoricalCalculationOrchestrator().process(
            synthetic_observation_batches(),
            weight_config=synthetic_weights(),
            observation_set_version_prefix=SYNTHETIC_OBSERVATION_VERSION,
        )
        reference = synthetic_reference_series()
        runner = BacktestRunner(
            reference_series_by_window=reference,
            reference_source_name=SYNTHETIC_REFERENCE_VERSION,
            is_official_reference=False,
            expected_window_days=SYNTHETIC_DAYS,
        )

        before_outputs = tuple(output.to_dict() for output in result.engine_outputs)
        backtest = runner.evaluate_window(
            result.calculated_series_by_window,
            start_date=SYNTHETIC_START_DATE,
            end_date=SYNTHETIC_START_DATE + timedelta(days=SYNTHETIC_DAYS - 1),
        )

        self.assertEqual(backtest.reference_source, SYNTHETIC_REFERENCE_VERSION)
        self.assertFalse(backtest.is_official_reference)
        self.assertEqual(backtest.expected_days, SYNTHETIC_DAYS)
        self.assertEqual(backtest.matched_days, SYNTHETIC_DAYS - 1)
        self.assertEqual(backtest.status, "COMPLETED")
        self.assertEqual(set(backtest.booking_window_metrics), set(BookingWindow))
        for metrics in backtest.booking_window_metrics.values():
            self.assertEqual(metrics.coverage.status, MetricStatus.VALID)
            self.assertAlmostEqual(
                metrics.coverage.value, (SYNTHETIC_DAYS - 1) / SYNTHETIC_DAYS
            )
            self.assertEqual(metrics.mae.status, MetricStatus.VALID)
            self.assertEqual(metrics.rmse.status, MetricStatus.VALID)

        self.assertEqual(backtest.to_dict()["reference_source"], SYNTHETIC_REFERENCE_VERSION)
        self.assertEqual(
            tuple(output.to_dict() for output in result.engine_outputs), before_outputs
        )

    def test_missing_calculated_day_reports_partial_coverage_without_filling(self):
        result = HistoricalCalculationOrchestrator().process(
            synthetic_observation_batches(),
            weight_config=synthetic_weights(),
            observation_set_version_prefix=SYNTHETIC_OBSERVATION_VERSION,
        )
        calculated = {
            window: dict(series)
            for window, series in result.calculated_series_by_window.items()
        }
        removed_date = SYNTHETIC_START_DATE + timedelta(days=10)
        for series in calculated.values():
            del series[removed_date]

        backtest = BacktestRunner(
            reference_series_by_window=synthetic_reference_series(),
            reference_source_name=SYNTHETIC_REFERENCE_VERSION,
            is_official_reference=False,
        ).evaluate_window(
            calculated,
            start_date=SYNTHETIC_START_DATE,
            end_date=SYNTHETIC_START_DATE + timedelta(days=SYNTHETIC_DAYS - 1),
        )

        self.assertEqual(backtest.matched_days, SYNTHETIC_DAYS - 2)
        self.assertTrue(backtest.warnings)
        self.assertAlmostEqual(
            backtest.booking_window_metrics[BookingWindow.T_7].coverage.value,
            (SYNTHETIC_DAYS - 2) / SYNTHETIC_DAYS,
        )
        self.assertNotIn(removed_date, calculated[BookingWindow.T_7])


if __name__ == "__main__":
    unittest.main()