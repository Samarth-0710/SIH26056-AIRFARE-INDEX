"""Pipeline Orchestrator for SIH26056 Airfare Price Index.

Executes the complete end-to-end flow:
1. Data Collection (Mock adapter or live Ignav adapter)
2. Data Quality & Normalization
3. Statistical Index Engine (Jevons elementary indices & national aggregation)
4. Intelligence Analysis (Anomaly and shock detection)
5. Database Persistence (Routes, observations, indices, quality, intelligence)
"""

from __future__ import annotations

import os
import time
from datetime import date, datetime, time as dtime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    FareObservation as DBFareObservation,
    IndexResult as DBIndexResult,
    IntelligenceEvent as DBIntelligenceEvent,
    MoSPIAirfareReference as DBMoSPIAirfareReference,
    QualityMetric as DBQualityMetric,
    Route as DBRoute,
    RouteIndex as DBRouteIndex,
)
from app.services.helpers import get_or_create_route

# Cross-module imports
from data_collection.models import RawFareRecord
from data_quality.bridge import (
    clean_and_convert_records,
    normalized_to_engine_observation,
    raw_record_to_raw_observation,
)
from data_quality.models import QualityStatus as DQQualityStatus
from data_quality.pipeline import run_pipeline as run_dq_pipeline
from intelligence.integration.statistical_engine_adapter import (
    StatisticalEngineIntelligenceAdapter,
)
from statistical_engine.engine import AirfareStatisticalEngine
from statistical_engine.models.observation import (
    BookingWindow as SEBookingWindow,
    FareObservation as EngineFareObservation,
    QualityStatus as SEQualityStatus,
)
from statistical_engine.models.weights import get_demo_reference_weights


def db_obs_to_engine_obs(db_obs: DBFareObservation) -> Optional[EngineFareObservation]:
    """Convert a persisted DBFareObservation into a statistical EngineFareObservation."""
    try:
        origin = db_obs.route.origin if db_obs.route else (db_obs.metadata_json or {}).get("origin")
        destination = db_obs.route.destination if db_obs.route else (db_obs.metadata_json or {}).get("destination")
        if not origin or not destination:
            if db_obs.route and "-" in db_obs.route.code:
                origin, destination = db_obs.route.code.split("-", 1)
        if not origin or not destination:
            return None

        bw = SEBookingWindow.from_string(db_obs.booking_window)
        qs = SEQualityStatus(db_obs.quality_status.upper()) if db_obs.quality_status else SEQualityStatus.VALID

        return EngineFareObservation(
            origin=origin,
            destination=destination,
            travel_date=db_obs.travel_date,
            observation_date=db_obs.observation_date,
            booking_window=bw,
            airline=db_obs.airline,
            flight_number=db_obs.flight_number,
            departure_time=str(db_obs.departure_time),
            cabin_class=db_obs.cabin_class,
            fare_type=db_obs.fare_type,
            baggage_characteristics=db_obs.baggage_characteristics,
            comparable_fare=float(db_obs.comparable_fare),
            source=db_obs.source,
            observation_timestamp=db_obs.observation_timestamp,
            quality_status=qs,
            metadata=db_obs.metadata_json or {},
        )
    except Exception:
        return None


def _persist_normalized_observations(
    db: Session,
    normalized_observations: List[Any],
    route_map: Dict[str, DBRoute],
) -> int:
    """Persist non-EXCLUDED normalized observations into fare_observations table."""
    persisted_count = 0
    for norm in normalized_observations:
        if norm.quality_status == DQQualityStatus.EXCLUDED or getattr(norm.quality_status, "value", norm.quality_status) == "EXCLUDED":
            continue

        existing = db.scalar(
            select(DBFareObservation.id).where(
                DBFareObservation.fingerprint == norm.fingerprint,
                DBFareObservation.observation_timestamp == norm.observation_timestamp,
                DBFareObservation.source == norm.source,
            )
        )
        if existing:
            continue

        r_code = f"{norm.origin}-{norm.destination}"
        route = route_map.get(r_code) or get_or_create_route(db, r_code)
        db_obs = DBFareObservation(
            route_id=route.id,
            observation_timestamp=norm.observation_timestamp,
            observation_date=norm.observation_date,
            travel_date=norm.travel_date,
            booking_window=norm.booking_window.value,
            airline=norm.airline,
            flight_number=norm.flight_number,
            departure_time=norm.departure_time,
            cabin_class=norm.cabin_class,
            fare_type=norm.fare_type,
            baggage_characteristics=norm.baggage_characteristics,
            base_fare=Decimal(str(norm.base_fare)) if norm.base_fare is not None else None,
            taxes=Decimal(str(norm.taxes)) if norm.taxes is not None else None,
            mandatory_charges=Decimal(str(norm.mandatory_charges)) if norm.mandatory_charges is not None else None,
            comparable_fare=Decimal(str(norm.comparable_fare or 0.0)),
            source=norm.source,
            fingerprint=norm.fingerprint,
            quality_status=norm.quality_status.value,
            metadata_json=norm.metadata,
        )
        db.add(db_obs)
        persisted_count += 1

    return persisted_count


DEFAULT_SAMPLE_ROUTES = [
    ("DEL", "BOM", 0.25, 4800.0),
    ("BOM", "DEL", 0.25, 4850.0),
    ("DEL", "BLR", 0.15, 5200.0),
    ("BLR", "DEL", 0.15, 5150.0),
    ("BOM", "BLR", 0.10, 4100.0),
    ("BLR", "BOM", 0.10, 4150.0),
]

BOOKING_WINDOW_LEAD_DAYS = {
    SEBookingWindow.T_1: 1,
    SEBookingWindow.T_7: 7,
    SEBookingWindow.T_15: 15,
    SEBookingWindow.T_30: 30,
    SEBookingWindow.T_45: 45,
}

# Lead time multipliers relative to base fare (shorter lead time -> higher fare)
WINDOW_FARE_MULTIPLIERS = {
    1: 1.45,   # T+1: last minute surge
    7: 1.20,   # T+7: 1 week out
    15: 1.05,  # T+15: 2 weeks out
    30: 0.95,  # T+30: 1 month advance
    45: 0.88,  # T+45: early bird saver
}


def generate_synthetic_records(
    observation_date: date,
    price_factor: float = 1.0,
    source: str = "mock",
) -> List[RawFareRecord]:
    """Generate deterministic, realistic flight records for testing and demo execution."""
    records: List[RawFareRecord] = []
    now = datetime.now(timezone.utc)

    flights = [
        ("IndiGo", "6E-201", dtime(6, 30), "SAVER"),
        ("Air India", "AI-102", dtime(11, 45), "REGULAR"),
        ("Akasa Air", "QP-303", dtime(18, 15), "SAVER"),
    ]

    for orig, dest, weight, base_price in DEFAULT_SAMPLE_ROUTES:
        for bw_enum, lead_days in BOOKING_WINDOW_LEAD_DAYS.items():
            travel_date = observation_date + timedelta(days=lead_days)
            lead_mult = WINDOW_FARE_MULTIPLIERS.get(lead_days, 1.0)

            for airline, flight_num, dep_time, fare_type in flights:
                # Airline adjustment
                airline_mult = 0.96 if airline == "Akasa Air" else (1.08 if airline == "Air India" else 1.0)
                amount = round(base_price * lead_mult * airline_mult * price_factor, 2)

                records.append(
                    RawFareRecord(
                        origin=orig,
                        destination=dest,
                        travel_date=travel_date,
                        observation_date=observation_date,
                        booking_window=lead_days,
                        airline=airline,
                        flight_number=flight_num,
                        departure_time=dep_time,
                        cabin_class="ECONOMY",
                        fare_type=fare_type,
                        baggage_characteristics="15KG",
                        fare_amount=amount,
                        currency="INR",
                        source=source,
                        observation_timestamp=now,
                        metadata={
                            "demo_synthetic": True,
                            "window_code": bw_enum.value,
                            "route_weight": weight,
                        },
                    )
                )

    return records


def load_mospi_reference_dataset(db: Session, excel_path: Optional[str | Path] = None) -> int:
    """Load the official MoSPI CPI Airfare reference dataset into mospi_airfare_reference table.

    Returns the count of persisted reference records.
    """
    from pathlib import Path
    from data_collection.mospi_adapter import MoSPIReferenceAdapter

    adapter = MoSPIReferenceAdapter(dataset_path=excel_path)
    if adapter.get_status() != "AVAILABLE":
        return 0

    records = adapter.get_national_series()

    loaded_count = 0
    for rec in records:
        exists = db.scalar(
            select(DBMoSPIAirfareReference).where(
                DBMoSPIAirfareReference.reference_date == rec.reference_date,
                DBMoSPIAirfareReference.item_code == rec.item_code,
                DBMoSPIAirfareReference.base_year == rec.base_year,
            )
        )
        if not exists:
            db_ref = DBMoSPIAirfareReference(
                reference_date=rec.reference_date,
                index_value=Decimal(str(rec.index_value)),
                item_code=rec.item_code,
                item=rec.item,
                base_year=rec.base_year,
                series=rec.series,
                source=rec.source,
                frequency=rec.frequency,
                state=rec.state,
                sector=rec.sector,
            )
            db.add(db_ref)
            loaded_count += 1

    db.commit()
    return loaded_count


def run_pipeline(
    db: Session,
    target_date: Optional[date] = None,
    use_live_source: bool = False,
    price_movement_pct: float = 2.5,
    days: int = 30,
    clean: bool = True,
    live_adapter: Optional[Any] = None,
) -> Dict[str, Any]:
    """Execute the full SIH26056 pipeline over a historical window and store outputs into the database."""
    end_date = target_date or date.today()
    run_timestamp = datetime.now(timezone.utc)

    # 1. Optionally clean previous demo/test records for idempotency (only in synthetic mode)
    if clean and not use_live_source:
        db.query(DBIntelligenceEvent).delete()
        db.query(DBQualityMetric).delete()
        db.query(DBRouteIndex).delete()
        db.query(DBIndexResult).delete()
        db.query(DBFareObservation).delete()
        db.commit()

    # Load official MoSPI CPI reference series (separate validation layer)
    mospi_count = load_mospi_reference_dataset(db)

    # 2. Ensure routes exist in DB
    route_map: Dict[str, DBRoute] = {}
    for orig, dest, _, _ in DEFAULT_SAMPLE_ROUTES:
        code = f"{orig}-{dest}"
        route_map[code] = get_or_create_route(db, code)

    # 3. Setup common components
    engine = AirfareStatisticalEngine(allow_partial_coverage=True)
    weights = get_demo_reference_weights()
    intel_adapter = StatisticalEngineIntelligenceAdapter()

    # =========================================================================
    # LIVE SOURCE BRANCH
    # =========================================================================
    if use_live_source:
        active_live_adapter = live_adapter
        if active_live_adapter is None:
            try:
                from data_collection.ignav_adapter import IgnavFareAdapter
                from data_collection.adapters import SourceStatus
                candidate = IgnavFareAdapter()
                if candidate.get_status() == SourceStatus.AVAILABLE:
                    active_live_adapter = candidate
            except Exception:
                active_live_adapter = None

        if active_live_adapter is None:
            raise RuntimeError(
                "Live data collection requested (use_live_source=True), but live source adapter is unavailable or unconfigured."
            )

        curr_date = end_date
        prev_date = curr_date - timedelta(days=1)
        sample_pairs = [(r[0], r[1]) for r in DEFAULT_SAMPLE_ROUTES]
        target_windows = [1, 7, 15, 30, 45]

        total_observations_stored = 0
        total_valid_observations = 0
        total_rejected_observations = 0

        # Step 2: Look in fare_observations for REAL IGNAV observations on prev_date
        existing_prev_db = (
            db.query(DBFareObservation)
            .options(joinedload(DBFareObservation.route))
            .filter(
                DBFareObservation.source == "IGNAV",
                DBFareObservation.observation_date == prev_date,
                DBFareObservation.quality_status != DQQualityStatus.EXCLUDED.value,
            )
            .all()
        )

        eng_prev: List[EngineFareObservation] = []
        is_cold_start = False

        if existing_prev_db:
            for r in existing_prev_db:
                converted = db_obs_to_engine_obs(r)
                if converted is not None and converted.quality_status == SEQualityStatus.VALID:
                    eng_prev.append(converted)

        # Step 3 & 4: If insufficient previous live obs exist in DB, cold-start
        if not eng_prev:
            is_cold_start = True
            raw_prev = active_live_adapter.collect_all(
                observation_date=prev_date,
                routes=sample_pairs,
                booking_windows=target_windows,
            )
            dq_prev = run_dq_pipeline(raw_prev)
            stored_prev = _persist_normalized_observations(db, dq_prev.normalized_observations, route_map)
            total_observations_stored += stored_prev
            total_valid_observations += dq_prev.valid_count
            total_rejected_observations += len(dq_prev.rejected_observations)

            eng_prev = [
                normalized_to_engine_observation(n)
                for n in dq_prev.normalized_observations
                if n.quality_status == DQQualityStatus.VALID and normalized_to_engine_observation(n)
            ]

            qm_prev = DBQualityMetric(
                metric_date=prev_date,
                source="IGNAV",
                observation_count=dq_prev.total_processed,
                route_coverage=Decimal("1.0000"),
                source_coverage=Decimal("1.0000"),
                freshness_minutes=1,
                missing_observations=len(dq_prev.rejected_observations),
                invalid_observations=0,
                anomalous_valid_observations=dq_prev.outlier_count,
                status="COMPLETE",
                generated_at=run_timestamp - timedelta(days=1),
            )
            db.add(qm_prev)

            # Record baseline index results (100.0) for prev_date on cold start
            prev_base_calc_version = f"CALC_{prev_date.isoformat()}_BASE"
            for bw_enum in SEBookingWindow:
                db_idx_prev = DBIndexResult(
                    observation_date=prev_date,
                    booking_window=bw_enum.value,
                    index_value=Decimal("100.0000"),
                    status="SUCCESS",
                    observation_set_version=f"OBS_{prev_date.isoformat()}",
                    basket_version="BASKET_v1.0",
                    weight_version=weights.version,
                    methodology_version=engine.methodology_version,
                    calculation_version=prev_base_calc_version,
                    execution_checksum="0" * 64,
                    calculation_timestamp=run_timestamp - timedelta(days=1),
                )
                db.add(db_idx_prev)
                db.flush()

                for r_code in sorted(weights.weights.keys()):
                    route = route_map.get(r_code) or get_or_create_route(db, r_code)
                    w = weights.weights.get(r_code, 0.0)
                    db_r_idx_prev = DBRouteIndex(
                        index_result_id=db_idx_prev.id,
                        route_id=route.id,
                        index_value=Decimal("100.0000"),
                        status="SUCCESS",
                        weight=Decimal(str(round(w, 8))),
                        contribution=Decimal("0.0000"),
                    )
                    db.add(db_r_idx_prev)

            db.flush()

        # Step 5: Collect current REAL live observations for curr_date
        raw_curr = active_live_adapter.collect_all(
            observation_date=curr_date,
            routes=sample_pairs,
            booking_windows=target_windows,
        )
        dq_curr = run_dq_pipeline(raw_curr)
        stored_curr = _persist_normalized_observations(db, dq_curr.normalized_observations, route_map)
        total_observations_stored += stored_curr
        total_valid_observations += dq_curr.valid_count
        total_rejected_observations += len(dq_curr.rejected_observations)

        eng_curr = [
            normalized_to_engine_observation(n)
            for n in dq_curr.normalized_observations
            if n.quality_status == DQQualityStatus.VALID and normalized_to_engine_observation(n)
        ]

        # Step 6: Previous route indices for chaining / contributions
        prev_route_indices: Dict[SEBookingWindow, Dict[str, float]] = {
            bw: {r: 100.0 for r in weights.weights} for bw in SEBookingWindow
        }
        prev_indices_db = (
            db.query(DBRouteIndex)
            .join(DBIndexResult, DBRouteIndex.index_result_id == DBIndexResult.id)
            .join(DBRoute, DBRouteIndex.route_id == DBRoute.id)
            .filter(DBIndexResult.observation_date == prev_date)
            .all()
        )
        for pri in prev_indices_db:
            try:
                bw = SEBookingWindow.from_string(pri.index_result.booking_window)
                if pri.route and pri.index_value is not None:
                    prev_route_indices[bw][pri.route.code] = float(pri.index_value)
            except Exception:
                pass

        # Step 7: Pass directly to the EXISTING frozen Statistical Engine
        calc_version = f"CALC_{curr_date.isoformat()}_{int(time.time())}_LIVE"
        calc_output = engine.calculate_daily_indices(
            current_observations=eng_curr,
            previous_observations=eng_prev,
            observation_date=curr_date,
            previous_observation_date=prev_date,
            weight_config=weights,
            observation_set_version=f"OBS_{curr_date.isoformat()}",
            basket_version="BASKET_v1.0",
            previous_route_indices=prev_route_indices,
        )

        # Step 8: Intelligence analysis
        intel_results = intel_adapter.analyze_windows(
            calc_output,
            previous_route_indices_by_window=prev_route_indices,
        )

        # Step 9: Persist index results and route indices
        national_indices_summary: Dict[str, float] = {}
        total_index_results_stored = 0
        total_route_indices_stored = 0

        for bw_enum, nat_res in calc_output.national_results.items():
            val = Decimal(str(round(nat_res.national_index, 4))) if nat_res.national_index is not None else None
            if val is not None:
                national_indices_summary[bw_enum.value] = float(val)

            db_idx = DBIndexResult(
                observation_date=curr_date,
                booking_window=bw_enum.value,
                index_value=val,
                status=nat_res.status.value,
                observation_set_version=calc_output.reproducibility.observation_set_version,
                basket_version=calc_output.reproducibility.basket_version,
                weight_version=calc_output.reproducibility.weight_version,
                methodology_version=calc_output.reproducibility.methodology_version,
                calculation_version=calc_version,
                execution_checksum=calc_output.reproducibility.execution_checksum,
                calculation_timestamp=run_timestamp,
            )
            db.add(db_idx)
            db.flush()
            total_index_results_stored += 1

            for r_code, r_res in calc_output.route_results.items():
                win_idx = r_res.window_indices.get(bw_enum)
                route = route_map.get(r_code) or get_or_create_route(db, r_code)
                r_val = Decimal(str(round(win_idx.index_value, 4))) if win_idx and win_idx.index_value is not None else None
                r_status = win_idx.status.value if win_idx else "INSUFFICIENT_DATA"
                w = weights.weights.get(r_code, 0.0)
                weight_dec = Decimal(str(round(w, 8))) if w else None

                contrib_obj = nat_res.route_contributions.get(r_code)
                contrib_val = None
                if contrib_obj:
                    if contrib_obj.point_contribution is not None:
                        contrib_val = contrib_obj.point_contribution
                    elif contrib_obj.level_contribution is not None:
                        contrib_val = contrib_obj.level_contribution
                contrib_dec = Decimal(str(round(contrib_val, 4))) if contrib_val is not None else None

                db_r_idx = DBRouteIndex(
                    index_result_id=db_idx.id,
                    route_id=route.id,
                    index_value=r_val,
                    status=r_status,
                    weight=weight_dec,
                    contribution=contrib_dec,
                )
                db.add(db_r_idx)
                total_route_indices_stored += 1

        # Store quality metric for curr_date
        qm_curr = DBQualityMetric(
            metric_date=curr_date,
            source="IGNAV",
            observation_count=dq_curr.total_processed,
            route_coverage=Decimal("1.0000"),
            source_coverage=Decimal("1.0000"),
            freshness_minutes=1,
            missing_observations=len(dq_curr.rejected_observations),
            invalid_observations=0,
            anomalous_valid_observations=dq_curr.outlier_count,
            status="COMPLETE",
            generated_at=run_timestamp,
        )
        db.add(qm_curr)

        # Store intelligence events
        total_intel_events_stored = 0
        for bw_enum, intel_out in intel_results.items():
            for anomaly in intel_out.anomalies:
                if anomaly.detected or (anomaly.anomaly_score is not None and abs(anomaly.anomaly_score) >= 3.0):
                    route = route_map.get(anomaly.route) if anomaly.route else None
                    is_shock = anomaly.detected and (anomaly.anomaly_score is not None and abs(anomaly.anomaly_score) >= 4.0)
                    evt = DBIntelligenceEvent(
                        route_id=route.id if route else None,
                        event_type="AIRFARE_SHOCK" if is_shock else "ANOMALY",
                        anomaly_score=Decimal(str(round(anomaly.anomaly_score, 4))) if anomaly.anomaly_score is not None else None,
                        pressure_score=Decimal(str(round(min(100.0, max(0.0, abs(anomaly.anomaly_score or 0.0) * 10.0 + 35.0)), 4))),
                        shock_status="ALERT" if is_shock else "NORMAL",
                        explanation=anomaly.reason or f"Price movement on {anomaly.route} for {bw_enum.value}",
                        affected_sources=["IGNAV"],
                        affected_routes=[anomaly.route] if anomaly.route else [],
                        model_version=intel_out.provenance.model_version,
                        event_timestamp=run_timestamp,
                    )
                    db.add(evt)
                    total_intel_events_stored += 1

        db.commit()

        checksum = calc_output.reproducibility.execution_checksum if calc_output else ("0" * 64)
        return {
            "status": "SUCCESS",
            "mode": "LIVE",
            "historical_days": 1 if not is_cold_start else 2,
            "cold_start": is_cold_start,
            "observation_date": curr_date.isoformat(),
            "previous_observation_date": prev_date.isoformat(),
            "calculation_version": calc_version,
            "national_indices": national_indices_summary,
            "observations_stored": total_observations_stored,
            "valid_observations": total_valid_observations,
            "rejected_observations": total_rejected_observations,
            "routes_processed": len(route_map),
            "index_results_stored": total_index_results_stored,
            "route_indices_stored": total_route_indices_stored,
            "intelligence_events_stored": total_intel_events_stored,
            "quality_metrics_stored": 2 if is_cold_start else 1,
            "mospi_reference_records": mospi_count,
            "execution_checksum": checksum,
        }

    # =========================================================================
    # SYNTHETIC / DEMO SIMULATION BRANCH (use_live_source=False)
    # =========================================================================
    from data_collection.mock_adapter import SyntheticFareAdapter
    synth_adapter = SyntheticFareAdapter()

    # Determine historical date range
    # Day 0 = base_date (base index 100.0)
    # Days 1..num_days = daily transitions
    num_days = max(1, days)
    base_date = end_date - timedelta(days=num_days)

    total_observations_stored = 0
    total_valid_observations = 0
    total_rejected_observations = 0

    # Collect base basket (Day 0)
    raw_base = synth_adapter.collect_basket(base_date, source="mock", day_offset=0)
    dq_base = run_dq_pipeline(raw_base)
    stored_base = _persist_normalized_observations(db, dq_base.normalized_observations, route_map)
    total_observations_stored += stored_base
    total_valid_observations += dq_base.valid_count
    total_rejected_observations += len(dq_base.rejected_observations)

    # Store base index results and route indices (Day 0, index=100.0)
    total_index_results_stored = 0
    total_route_indices_stored = 0
    base_calc_version = f"CALC_{base_date.isoformat()}_BASE"

    for bw_enum in SEBookingWindow:
        db_idx = DBIndexResult(
            observation_date=base_date,
            booking_window=bw_enum.value,
            index_value=Decimal("100.0000"),
            status="SUCCESS",
            observation_set_version="OBS_BASE",
            basket_version="BASKET_v1.0",
            weight_version=weights.version,
            methodology_version=engine.methodology_version,
            calculation_version=base_calc_version,
            execution_checksum="0" * 64,
            calculation_timestamp=run_timestamp - timedelta(days=num_days),
        )
        db.add(db_idx)
        db.flush()
        total_index_results_stored += 1

        for r_code in sorted(weights.weights.keys()):
            route = route_map.get(r_code) or get_or_create_route(db, r_code)
            w = weights.weights.get(r_code, 0.0)
            db_r_idx = DBRouteIndex(
                index_result_id=db_idx.id,
                route_id=route.id,
                index_value=Decimal("100.0000"),
                status="SUCCESS",
                weight=Decimal(str(round(w, 8))),
                contribution=Decimal("0.0000"),
            )
            db.add(db_r_idx)
            total_route_indices_stored += 1

    # Store base quality metric
    qm_base = DBQualityMetric(
        metric_date=base_date,
        source="MOCK",
        observation_count=dq_base.total_processed,
        route_coverage=Decimal("1.0000"),
        source_coverage=Decimal("1.0000"),
        freshness_minutes=1,
        missing_observations=len(dq_base.rejected_observations),
        invalid_observations=0,
        anomalous_valid_observations=dq_base.outlier_count,
        status="COMPLETE",
        generated_at=run_timestamp - timedelta(days=num_days),
    )
    db.add(qm_base)

    # Base engine observations
    eng_base: List[EngineFareObservation] = [
        normalized_to_engine_observation(n)
        for n in dq_base.normalized_observations
        if n.quality_status == DQQualityStatus.VALID and normalized_to_engine_observation(n)
    ]

    # Initialize tracking of previous route indices for day-over-day changes
    prev_route_indices = {
        bw: {r: 100.0 for r in weights.weights} for bw in SEBookingWindow
    }

    total_intel_events_stored = 0
    last_calc_output = None
    last_calc_version = base_calc_version
    national_indices_summary = {}

    # Multi-day loop: Days 1 to num_days
    for day_offset in range(1, num_days + 1):
        curr_date = base_date + timedelta(days=day_offset)
        calc_version = f"CALC_{curr_date.isoformat()}_{int(time.time())}_{day_offset}"
        day_timestamp = run_timestamp - timedelta(days=num_days - day_offset)

        raw_curr = synth_adapter.collect_basket(curr_date, day_offset=day_offset, source="mock")

        # Data Quality
        dq_curr = run_dq_pipeline(raw_curr)
        eng_curr = [
            normalized_to_engine_observation(n)
            for n in dq_curr.normalized_observations
            if n.quality_status == DQQualityStatus.VALID and normalized_to_engine_observation(n)
        ]

        # Statistical Engine Calculation
        calc_output = engine.calculate_daily_indices(
            current_observations=eng_curr,
            previous_observations=eng_base,
            observation_date=curr_date,
            previous_observation_date=base_date,
            weight_config=weights,
            observation_set_version=f"OBS_{curr_date.isoformat()}",
            basket_version="BASKET_v1.0",
            previous_route_indices=prev_route_indices,
        )
        last_calc_output = calc_output
        last_calc_version = calc_version

        # Intelligence Layer
        intel_results = intel_adapter.analyze_windows(
            calc_output,
            previous_route_indices_by_window=prev_route_indices,
        )

        # Store current observations
        stored_curr = _persist_normalized_observations(db, dq_curr.normalized_observations, route_map)
        total_observations_stored += stored_curr
        total_valid_observations += dq_curr.valid_count
        total_rejected_observations += len(dq_curr.rejected_observations)

        # Store index results and route indices
        for bw_enum, nat_res in calc_output.national_results.items():
            val = Decimal(str(round(nat_res.national_index, 4))) if nat_res.national_index is not None else None
            if day_offset == num_days and val is not None:
                national_indices_summary[bw_enum.value] = float(val)

            db_idx = DBIndexResult(
                observation_date=curr_date,
                booking_window=bw_enum.value,
                index_value=val,
                status=nat_res.status.value,
                observation_set_version=calc_output.reproducibility.observation_set_version,
                basket_version=calc_output.reproducibility.basket_version,
                weight_version=calc_output.reproducibility.weight_version,
                methodology_version=calc_output.reproducibility.methodology_version,
                calculation_version=calc_version,
                execution_checksum=calc_output.reproducibility.execution_checksum,
                calculation_timestamp=day_timestamp,
            )
            db.add(db_idx)
            db.flush()
            total_index_results_stored += 1

            for r_code, r_res in calc_output.route_results.items():
                win_idx = r_res.window_indices.get(bw_enum)
                route = route_map.get(r_code) or get_or_create_route(db, r_code)
                r_val = Decimal(str(round(win_idx.index_value, 4))) if win_idx and win_idx.index_value is not None else None
                r_status = win_idx.status.value if win_idx else "INSUFFICIENT_DATA"
                w = weights.weights.get(r_code, 0.0)
                weight_dec = Decimal(str(round(w, 8))) if w else None

                contrib_obj = nat_res.route_contributions.get(r_code)
                contrib_val = None
                if contrib_obj:
                    if contrib_obj.point_contribution is not None:
                        contrib_val = contrib_obj.point_contribution
                    elif contrib_obj.level_contribution is not None:
                        contrib_val = contrib_obj.level_contribution
                contrib_dec = Decimal(str(round(contrib_val, 4))) if contrib_val is not None else None

                db_r_idx = DBRouteIndex(
                    index_result_id=db_idx.id,
                    route_id=route.id,
                    index_value=r_val,
                    status=r_status,
                    weight=weight_dec,
                    contribution=contrib_dec,
                )
                db.add(db_r_idx)
                total_route_indices_stored += 1

        # Store quality metric
        qm = DBQualityMetric(
            metric_date=curr_date,
            source="MOCK",
            observation_count=dq_curr.total_processed,
            route_coverage=Decimal("1.0000"),
            source_coverage=Decimal("1.0000"),
            freshness_minutes=1,
            missing_observations=len(dq_curr.rejected_observations),
            invalid_observations=0,
            anomalous_valid_observations=dq_curr.outlier_count,
            status="COMPLETE",
            generated_at=day_timestamp,
        )
        db.add(qm)

        # Store intelligence events
        for bw_enum, intel_out in intel_results.items():
            for anomaly in intel_out.anomalies:
                if anomaly.detected or (anomaly.anomaly_score is not None and abs(anomaly.anomaly_score) >= 3.0):
                    route = route_map.get(anomaly.route) if anomaly.route else None
                    is_shock = anomaly.detected and (anomaly.anomaly_score is not None and abs(anomaly.anomaly_score) >= 4.0)
                    evt = DBIntelligenceEvent(
                        route_id=route.id if route else None,
                        event_type="AIRFARE_SHOCK" if is_shock else "ANOMALY",
                        anomaly_score=Decimal(str(round(anomaly.anomaly_score, 4))) if anomaly.anomaly_score is not None else None,
                        pressure_score=Decimal(str(round(min(100.0, max(0.0, abs(anomaly.anomaly_score or 0.0) * 10.0 + 35.0)), 4))),
                        shock_status="ALERT" if is_shock else "NORMAL",
                        explanation=anomaly.reason or f"Price movement on {anomaly.route} for {bw_enum.value}",
                        affected_sources=["MOCK"],
                        affected_routes=[anomaly.route] if anomaly.route else [],
                        model_version=intel_out.provenance.model_version,
                        event_timestamp=day_timestamp,
                    )
                    db.add(evt)
                    total_intel_events_stored += 1

        # Update previous route indices for the next iteration
        for bw in SEBookingWindow:
            for r, r_res in calc_output.route_results.items():
                win_idx = r_res.window_indices.get(bw)
                if win_idx and win_idx.index_value is not None:
                    prev_route_indices[bw][r] = float(win_idx.index_value)

    db.commit()

    checksum = last_calc_output.reproducibility.execution_checksum if last_calc_output else ("0" * 64)

    return {
        "status": "SUCCESS",
        "mode": "SYNTHETIC",
        "historical_days": num_days,
        "observation_date": end_date.isoformat(),
        "previous_observation_date": base_date.isoformat(),
        "calculation_version": last_calc_version,
        "national_indices": national_indices_summary,
        "observations_stored": total_observations_stored,
        "valid_observations": total_valid_observations,
        "rejected_observations": total_rejected_observations,
        "routes_processed": len(route_map),
        "index_results_stored": total_index_results_stored,
        "route_indices_stored": total_route_indices_stored,
        "intelligence_events_stored": total_intel_events_stored,
        "quality_metrics_stored": num_days + 1,
        "mospi_reference_records": mospi_count,
        "execution_checksum": checksum,
    }
