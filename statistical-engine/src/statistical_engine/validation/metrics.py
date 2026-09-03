"""Statistical validation metrics implementation for airfare index evaluation.

Implements documented validation metrics:
- Pearson Correlation (r)
- Spearman Rank Correlation (rho)
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Directional Accuracy
- Coverage
- Stability (volatility of daily changes)

Handles edge cases: constant series (zero variance), missing data, NaN/Inf, mismatched lengths.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from statistical_engine.models.validation_result import (
    MetricStatus,
    MetricValue,
    ValidationMetrics,
)


def _rank_data(values: Sequence[float]) -> List[float]:
    """Assign fractional ranks to data, resolving ties with average ranks."""
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    n = len(indexed)
    while i < n:
        j = i
        while j + 1 < n and indexed[j + 1][1] == indexed[j][1]:
            j += 1
        # average rank for tie group (1-indexed)
        avg_rank = sum(range(i + 1, j + 2)) / (j - i + 1)
        for k in range(i, j + 1):
            orig_idx = indexed[k][0]
            ranks[orig_idx] = avg_rank
        i = j + 1
    return ranks


def calculate_pearson_correlation(
    series_a: Sequence[float],
    series_b: Sequence[float],
) -> MetricValue:
    """Calculate Pearson correlation coefficient r between two paired series."""
    if len(series_a) != len(series_b):
        return MetricValue(
            name="pearson_correlation",
            value=None,
            status=MetricStatus.MISMATCHED_LENGTH,
            sample_size=min(len(series_a), len(series_b)),
            note=f"Series lengths mismatch: {len(series_a)} vs {len(series_b)}",
        )

    # Filter out pairs containing NaN or Inf
    valid_pairs = [
        (float(a), float(b))
        for a, b in zip(series_a, series_b)
        if not (math.isnan(a) or math.isnan(b) or math.isinf(a) or math.isinf(b))
    ]

    n = len(valid_pairs)
    if n < 2:
        return MetricValue(
            name="pearson_correlation",
            value=None,
            status=MetricStatus.INSUFFICIENT_DATA,
            sample_size=n,
            note="At least 2 valid paired observations required",
        )

    x = [p[0] for p in valid_pairs]
    y = [p[1] for p in valid_pairs]

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in valid_pairs)
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    if var_x == 0.0 or var_y == 0.0:
        return MetricValue(
            name="pearson_correlation",
            value=None,
            status=MetricStatus.UNDEFINED_VARIANCE,
            sample_size=n,
            note="Zero variance detected: one or both series are constant",
        )

    r = cov_xy / math.sqrt(var_x * var_y)
    # Clamp floating point edge cases to [-1.0, 1.0]
    r_clamped = max(-1.0, min(1.0, r))

    return MetricValue(
        name="pearson_correlation",
        value=r_clamped,
        status=MetricStatus.VALID,
        sample_size=n,
    )


def calculate_spearman_correlation(
    series_a: Sequence[float],
    series_b: Sequence[float],
) -> MetricValue:
    """Calculate Spearman rank correlation coefficient rho between two paired series."""
    if len(series_a) != len(series_b):
        return MetricValue(
            name="spearman_correlation",
            value=None,
            status=MetricStatus.MISMATCHED_LENGTH,
            sample_size=min(len(series_a), len(series_b)),
            note=f"Series lengths mismatch: {len(series_a)} vs {len(series_b)}",
        )

    valid_pairs = [
        (float(a), float(b))
        for a, b in zip(series_a, series_b)
        if not (math.isnan(a) or math.isnan(b) or math.isinf(a) or math.isinf(b))
    ]

    n = len(valid_pairs)
    if n < 2:
        return MetricValue(
            name="spearman_correlation",
            value=None,
            status=MetricStatus.INSUFFICIENT_DATA,
            sample_size=n,
            note="At least 2 valid paired observations required",
        )

    x = [p[0] for p in valid_pairs]
    y = [p[1] for p in valid_pairs]

    rank_x = _rank_data(x)
    rank_y = _rank_data(y)

    pearson_on_ranks = calculate_pearson_correlation(rank_x, rank_y)
    return MetricValue(
        name="spearman_correlation",
        value=pearson_on_ranks.value,
        status=pearson_on_ranks.status,
        sample_size=n,
        note=pearson_on_ranks.note,
    )


def calculate_mae(
    predictions: Sequence[float],
    reference: Sequence[float],
) -> MetricValue:
    """Calculate Mean Absolute Error: (1/n) * sum(|pred - ref|)."""
    if len(predictions) != len(reference):
        return MetricValue(
            name="mae",
            value=None,
            status=MetricStatus.MISMATCHED_LENGTH,
            sample_size=min(len(predictions), len(reference)),
            note="Series lengths mismatch",
        )

    valid_diffs = [
        abs(float(p) - float(r))
        for p, r in zip(predictions, reference)
        if not (math.isnan(p) or math.isnan(r) or math.isinf(p) or math.isinf(r))
    ]

    n = len(valid_diffs)
    if n == 0:
        return MetricValue(
            name="mae",
            value=None,
            status=MetricStatus.INSUFFICIENT_DATA,
            sample_size=0,
            note="Zero valid pairs for MAE calculation",
        )

    mae_val = sum(valid_diffs) / n
    return MetricValue(
        name="mae",
        value=mae_val,
        status=MetricStatus.VALID,
        sample_size=n,
    )


def calculate_rmse(
    predictions: Sequence[float],
    reference: Sequence[float],
) -> MetricValue:
    """Calculate Root Mean Squared Error: sqrt((1/n) * sum((pred - ref)^2))."""
    if len(predictions) != len(reference):
        return MetricValue(
            name="rmse",
            value=None,
            status=MetricStatus.MISMATCHED_LENGTH,
            sample_size=min(len(predictions), len(reference)),
            note="Series lengths mismatch",
        )

    sq_errors = [
        (float(p) - float(r)) ** 2
        for p, r in zip(predictions, reference)
        if not (math.isnan(p) or math.isnan(r) or math.isinf(p) or math.isinf(r))
    ]

    n = len(sq_errors)
    if n == 0:
        return MetricValue(
            name="rmse",
            value=None,
            status=MetricStatus.INSUFFICIENT_DATA,
            sample_size=0,
            note="Zero valid pairs for RMSE calculation",
        )

    rmse_val = math.sqrt(sum(sq_errors) / n)
    return MetricValue(
        name="rmse",
        value=rmse_val,
        status=MetricStatus.VALID,
        sample_size=n,
    )


def calculate_directional_accuracy(
    predictions: Sequence[float],
    reference: Sequence[float],
) -> MetricValue:
    """Calculate Directional Accuracy: proportion of day-to-day changes with identical signs."""
    if len(predictions) != len(reference):
        return MetricValue(
            name="directional_accuracy",
            value=None,
            status=MetricStatus.MISMATCHED_LENGTH,
            sample_size=min(len(predictions), len(reference)),
            note="Series lengths mismatch",
        )

    valid_pairs = [
        (float(p), float(r))
        for p, r in zip(predictions, reference)
        if not (math.isnan(p) or math.isnan(r) or math.isinf(p) or math.isinf(r))
    ]

    n = len(valid_pairs)
    if n < 2:
        return MetricValue(
            name="directional_accuracy",
            value=None,
            status=MetricStatus.INSUFFICIENT_DATA,
            sample_size=n,
            note="At least 2 points required to calculate direction of change",
        )

    matches = 0
    total_eval = 0

    for i in range(1, n):
        d_pred = valid_pairs[i][0] - valid_pairs[i - 1][0]
        d_ref = valid_pairs[i][1] - valid_pairs[i - 1][1]

        # sign determination (-1, 0, 1)
        s_pred = 1 if d_pred > 1e-7 else (-1 if d_pred < -1e-7 else 0)
        s_ref = 1 if d_ref > 1e-7 else (-1 if d_ref < -1e-7 else 0)

        if s_pred == s_ref:
            matches += 1
        total_eval += 1

    accuracy = matches / total_eval if total_eval > 0 else 0.0
    return MetricValue(
        name="directional_accuracy",
        value=accuracy,
        status=MetricStatus.VALID,
        sample_size=total_eval,
    )


def calculate_coverage(
    valid_observed_days: int,
    expected_calendar_days: int,
) -> MetricValue:
    """Calculate temporal coverage ratio: valid_days / expected_days."""
    if expected_calendar_days <= 0:
        return MetricValue(
            name="coverage",
            value=None,
            status=MetricStatus.INVALID_SERIES,
            sample_size=valid_observed_days,
            note=f"Expected days must be > 0, got {expected_calendar_days}",
        )

    cov = min(1.0, max(0.0, valid_observed_days / expected_calendar_days))
    return MetricValue(
        name="coverage",
        value=cov,
        status=MetricStatus.VALID,
        sample_size=valid_observed_days,
    )


def calculate_stability(
    series: Sequence[float],
) -> MetricValue:
    """Calculate stability metric: sample standard deviation of period-to-period differences."""
    valid_vals = [
        float(x)
        for x in series
        if not (math.isnan(x) or math.isinf(x))
    ]

    n = len(valid_vals)
    if n < 3:
        return MetricValue(
            name="stability",
            value=None,
            status=MetricStatus.INSUFFICIENT_DATA,
            sample_size=n,
            note="At least 3 observations required to calculate change volatility",
        )

    diffs = [valid_vals[i] - valid_vals[i - 1] for i in range(1, n)]
    m = len(diffs)
    mean_diff = sum(diffs) / m
    var_diff = sum((d - mean_diff) ** 2 for d in diffs) / (m - 1)
    std_diff = math.sqrt(var_diff)

    return MetricValue(
        name="stability",
        value=std_diff,
        status=MetricStatus.VALID,
        sample_size=m,
        note="Sample standard deviation of first differences",
    )


def compute_all_validation_metrics(
    calculated_series: Sequence[float],
    reference_series: Sequence[float],
    expected_calendar_days: int = 30,
) -> ValidationMetrics:
    """Compute the full set of documented validation metrics between calculated and reference series."""
    pearson = calculate_pearson_correlation(calculated_series, reference_series)
    spearman = calculate_spearman_correlation(calculated_series, reference_series)
    mae = calculate_mae(calculated_series, reference_series)
    rmse = calculate_rmse(calculated_series, reference_series)
    dir_acc = calculate_directional_accuracy(calculated_series, reference_series)
    coverage = calculate_coverage(len(calculated_series), expected_calendar_days)
    stability = calculate_stability(calculated_series)

    return ValidationMetrics(
        pearson_correlation=pearson,
        spearman_correlation=spearman,
        mae=mae,
        rmse=rmse,
        directional_accuracy=dir_acc,
        coverage=coverage,
        stability=stability,
    )
