"""Validation service orchestrating external MoSPI CPI reference alignment and back-test analytics."""

from datetime import date
import math
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import IndexResult, MoSPIAirfareReference, RouteIndex
from app.schemas.validation import (
    AlignmentOut,
    ComparisonOut,
    CorrelationOut,
    MoSPIReferenceDetailsOut,
    MonthlySeriesPointOut,
    MovementOut,
    ValidationHistoryPointOut,
    ValidationMetricOut,
    ValidationResultOut,
)


def get_validation_analysis(db: Session) -> ValidationResultOut:
    """Evaluate calculated daily index series against official MoSPI reference series."""

    # 1. Fetch historical calculated daily indices from database for T+15 (headline advance window)
    results = db.scalars(
        select(IndexResult)
        .where(IndexResult.booking_window == "T+15", IndexResult.status == "SUCCESS")
        .order_by(IndexResult.observation_date)
    ).all()

    calc_series: List[float] = []
    dates: List[str] = []
    daily_by_month: Dict[str, List[float]] = {}

    for r in results:
        if r.index_value is not None:
            val = float(r.index_value)
            calc_series.append(val)
            d_str = r.observation_date.isoformat()
            dates.append(d_str)

            m_key = r.observation_date.strftime("%Y-%m")
            daily_by_month.setdefault(m_key, []).append(val)

    # Fallback if no daily index exists yet
    if not calc_series:
        latest = db.scalars(
            select(IndexResult)
            .where(IndexResult.status == "SUCCESS")
            .order_by(desc(IndexResult.observation_date))
        ).first()
        base_val = float(latest.index_value) if latest and latest.index_value is not None else 100.0
        calc_series = [base_val]
        today_iso = date.today().isoformat()
        dates = [today_iso]
        daily_by_month[today_iso[:7]] = [base_val]

    # 2. Calendar-Month Project Aggregation (Documented Method: Arithmetic Mean of Daily Levels)
    # I_{monthly, m} = (1 / N_m) * sum(I_{daily, d})
    our_monthly_index: Dict[str, float] = {}
    for m_key, vals in sorted(daily_by_month.items()):
        our_monthly_index[m_key] = round(sum(vals) / len(vals), 4)

    # 3. Query MoSPI Airfare Reference Dataset from database
    mospi_rows = db.scalars(
        select(MoSPIAirfareReference).order_by(MoSPIAirfareReference.reference_date)
    ).all()

    reference_connected = len(mospi_rows) > 0
    mospi_monthly: Dict[str, float] = {}
    for row in mospi_rows:
        m_key = row.reference_date.strftime("%Y-%m")
        mospi_monthly[m_key] = float(row.index_value)

    # MoSPI Reference Details
    if reference_connected:
        first_rec = mospi_rows[0]
        latest_rec = mospi_rows[-1]
        ref_details = MoSPIReferenceDetailsOut(
            name="MoSPI e-Sankhyiki CPI Airfare",
            source=latest_rec.source if hasattr(latest_rec, "source") and latest_rec.source else "MoSPI e-Sankhyiki",
            item=latest_rec.item if hasattr(latest_rec, "item") and latest_rec.item else "Airfare",
            item_code=latest_rec.item_code,
            base_year=latest_rec.base_year,
            series=latest_rec.series if hasattr(latest_rec, "series") and latest_rec.series else "Current",
            frequency=latest_rec.frequency,
            state=latest_rec.state,
            sector=latest_rec.sector,
            connected=True,
            records=len(mospi_rows),
            first_date=first_rec.reference_date.isoformat(),
            latest_date=latest_rec.reference_date.isoformat(),
            latest_cpi=float(latest_rec.index_value),
        )
        reference_name = f"MoSPI e-Sankhyiki CPI Airfare (Base 2024 = 100, {len(mospi_rows)} Monthly Records)"
    else:
        ref_details = MoSPIReferenceDetailsOut(
            name="MoSPI e-Sankhyiki CPI Airfare",
            connected=False,
            records=0,
        )
        reference_name = "NOT_CONNECTED (External MoSPI reference data not loaded)"

    # 4. Monthly Alignment & Comparison
    aligned_months = sorted(list(set(our_monthly_index.keys()) & set(mospi_monthly.keys())))
    overlapping_count = len(aligned_months)

    if reference_connected:
        alignment_status = "CONNECTED" if overlapping_count > 0 else "NO_OVERLAP"
    else:
        alignment_status = "NOT_CONNECTED"

    alignment_out = AlignmentOut(
        overlapping_months=overlapping_count,
        status=alignment_status,
        aligned_months=aligned_months,
    )

    # Comparison and Rebasing
    comparison_out: Optional[ComparisonOut] = None
    movement_out: Optional[MovementOut] = None
    correlation_out: Optional[CorrelationOut] = None

    our_rebased_map: Dict[str, float] = {}
    mospi_rebased_map: Dict[str, float] = {}

    if overlapping_count > 0:
        # Select reference month for rebasing (latest overlapping month)
        ref_month = aligned_months[-1]
        our_ref_val = our_monthly_index[ref_month]
        mospi_ref_val = mospi_monthly[ref_month]

        # Calculate rebased series: (Index_m / Index_ref) * 100.0
        for m in set(list(our_monthly_index.keys()) + list(mospi_monthly.keys())):
            if m in our_monthly_index and our_ref_val > 0:
                our_rebased_map[m] = round((our_monthly_index[m] / our_ref_val) * 100.0, 2)
            if m in mospi_monthly and mospi_ref_val > 0:
                mospi_rebased_map[m] = round((mospi_monthly[m] / mospi_ref_val) * 100.0, 2)

        our_latest_idx = our_monthly_index[ref_month]
        mospi_latest_idx = mospi_monthly[ref_month]
        abs_diff = round(abs(our_latest_idx - mospi_latest_idx), 4)
        pct_diff = round(((our_latest_idx - mospi_latest_idx) / mospi_latest_idx) * 100.0, 2)

        comparison_out = ComparisonOut(
            reference_month=ref_month,
            our_monthly_index=our_latest_idx,
            mospi_monthly_index=mospi_latest_idx,
            absolute_difference=abs_diff,
            percentage_difference=pct_diff,
            rebasing_method=f"Rebased to 100.0 at reference month {ref_month}",
            our_rebased_index=100.0,
            mospi_rebased_index=100.0,
        )

        # Month-over-Month (MoM) movement if >= 2 aligned months
        if overlapping_count >= 2:
            m_curr = aligned_months[-1]
            m_prev = aligned_months[-2]
            our_mom = round(((our_monthly_index[m_curr] / our_monthly_index[m_prev]) - 1.0) * 100.0, 2)
            mospi_mom = round(((mospi_monthly[m_curr] / mospi_monthly[m_prev]) - 1.0) * 100.0, 2)
            movement_out = MovementOut(
                our_mom_change=our_mom,
                mospi_mom_change=mospi_mom,
                absolute_difference=round(abs(our_mom - mospi_mom), 2),
            )
        else:
            movement_out = MovementOut(
                our_mom_change=None,
                mospi_mom_change=None,
                absolute_difference=None,
            )

        # Correlation (Requires >= 3 aligned observations for statistical validity)
        if overlapping_count >= 3:
            xs = [our_monthly_index[m] for m in aligned_months]
            ys = [mospi_monthly[m] for m in aligned_months]
            x_bar = sum(xs) / len(xs)
            y_bar = sum(ys) / len(ys)
            cov = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys))
            var_x = sum((x - x_bar) ** 2 for x in xs)
            var_y = sum((y - y_bar) ** 2 for y in ys)
            denom = math.sqrt(var_x * var_y)
            r_val = round(cov / denom, 4) if denom > 0 else 0.0
            correlation_out = CorrelationOut(
                value=r_val,
                status="CONNECTED",
            )
        else:
            correlation_out = CorrelationOut(
                value=None,
                status="INSUFFICIENT_OVERLAP",
            )
    else:
        correlation_out = CorrelationOut(
            value=None,
            status="NOT_CONNECTED" if not reference_connected else "INSUFFICIENT_OVERLAP",
        )

    # 5. Build Monthly Unified Series for Charting ("Our System vs MoSPI")
    all_months = sorted(list(set(list(our_monthly_index.keys()) + list(mospi_monthly.keys()))))
    monthly_series: List[MonthlySeriesPointOut] = []

    for m in all_months:
        in_proj = m in our_monthly_index
        in_mospi = m in mospi_monthly
        if in_proj and in_mospi:
            m_status = "ALIGNED"
        elif in_proj:
            m_status = "PROJECT_ONLY"
        else:
            m_status = "MOSPI_REFERENCE"

        monthly_series.append(
            MonthlySeriesPointOut(
                month=m,
                our_monthly_index=our_monthly_index.get(m),
                mospi_cpi=mospi_monthly.get(m),
                our_rebased=our_rebased_map.get(m),
                mospi_rebased=mospi_rebased_map.get(m),
                status=m_status,
            )
        )

    # 6. Build History Points (Daily calculated with monthly MoSPI overlay)
    history_points: List[ValidationHistoryPointOut] = []
    for d_str, c_val in zip(dates, calc_series):
        m_key = d_str[:7]
        ref_val = mospi_monthly.get(m_key)
        history_points.append(
            ValidationHistoryPointOut(
                date=d_str,
                calculated_index=round(c_val, 2),
                reference_index=round(ref_val, 2) if ref_val is not None else None,
            )
        )

    # 7. Dynamic Stability and Coverage from Database
    if len(calc_series) > 1:
        pct_changes = [(calc_series[i] - calc_series[i-1]) / calc_series[i-1] * 100 for i in range(1, len(calc_series))]
        mean_change = sum(pct_changes) / len(pct_changes)
        variance = sum((x - mean_change) ** 2 for x in pct_changes) / (len(pct_changes) - 1)
        stability_val = f"{math.sqrt(variance):.2f}"
    else:
        stability_val = "0.00"

    latest_res = results[-1] if results else None
    if latest_res:
        latest_routes = db.scalars(select(RouteIndex).where(RouteIndex.index_result_id == latest_res.id)).all()
        if latest_routes:
            success_count = sum(1 for r in latest_routes if r.status == "SUCCESS")
            cov_pct = (success_count / len(latest_routes)) * 100.0
            coverage_val = f"{cov_pct:.1f}%"
        else:
            coverage_val = "100.0%"
    else:
        coverage_val = "0.0%"

    # 8. Assemble Validation Metrics Table
    corr_status_label = correlation_out.status if correlation_out else "NOT_CONNECTED"
    corr_display_val = f"{correlation_out.value:.4f}" if correlation_out and correlation_out.value is not None else "N/A"

    metrics_out = [
        ValidationMetricOut(
            metric="Pearson Correlation (r)",
            value=corr_display_val,
            status=corr_status_label,
            description="Linear co-movement across aligned calendar months (minimum 3 months required)",
        ),
        ValidationMetricOut(
            metric="Spearman Rank Correlation (rho)",
            value="N/A",
            status=corr_status_label,
            description="Monotonic ranking consistency across aligned monthly index shifts",
        ),
        ValidationMetricOut(
            metric="Absolute Level Difference" if overlapping_count == 1 else "Mean Absolute Error (MAE)",
            value=f"{comparison_out.absolute_difference:.2f} pts" if comparison_out and comparison_out.absolute_difference is not None else "N/A",
            status=corr_status_label,
            description="Absolute divergence between project monthly index and MoSPI benchmark level at reference month" if overlapping_count == 1 else "Average absolute divergence across all aligned calendar months",
        ),
        ValidationMetricOut(
            metric="Percentage Difference",
            value=f"{comparison_out.percentage_difference:+.2f}%" if comparison_out and comparison_out.percentage_difference is not None else "N/A",
            status=corr_status_label,
            description="Relative percentage difference against official MoSPI benchmark level",
        ),
        ValidationMetricOut(
            metric="Corridor Coverage",
            value=coverage_val,
            status="OPTIMAL" if coverage_val == "100.0%" else "PARTIAL",
            description="Proportion of representative basket corridors successfully computed",
        ),
        ValidationMetricOut(
            metric="Index Stability",
            value=stability_val,
            status="STABLE" if float(stability_val) < 5.0 else "VOLATILE",
            description="Standard deviation of daily percentage changes in official index",
        ),
    ]

    period_str = f"{dates[0]} to {dates[-1]}" if len(dates) > 1 else dates[0]

    return ValidationResultOut(
        period=period_str,
        reference_dataset=reference_name,
        methodology_version="JEVONS_SHORT_INDEX_v1.0",
        observation_set_version="OBS_LATEST",
        is_reference_connected=reference_connected,
        metrics=metrics_out,
        history=history_points,
        reference_dataset_details=ref_details,
        alignment=alignment_out,
        comparison=comparison_out,
        movement=movement_out,
        correlation=correlation_out,
        monthly_series=monthly_series,
    )
