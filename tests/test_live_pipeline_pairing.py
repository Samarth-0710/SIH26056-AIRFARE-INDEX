"""Tests for Real Previous-Period Live Architecture (Tests A, B, C, E).

Verifies:
A. Two-period live pairing test with real-shaped observations (>0 comparable pairs, Statistical Engine SUCCESS)
B. Cold-start integration test (when DB has no prev_date live obs, both dates collected & persisted)
C. Incremental integration test (when DB already has prev_date live obs, loaded from DB without collecting prev_date)
E. Database integrity (no EXCLUDED rows inserted, no duplicate constraint errors)
"""

from datetime import date, datetime, time as dtime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import (
    FareObservation as DBFareObservation,
    IndexResult as DBIndexResult,
    Route as DBRoute,
    RouteIndex as DBRouteIndex,
)
from app.services.pipeline_service import (
    DEFAULT_SAMPLE_ROUTES,
    db_obs_to_engine_obs,
    run_pipeline,
)
from data_collection.adapters import SourceStatus
from data_collection.models import RawFareRecord
from data_quality.bridge import (
    clean_and_convert_records,
    normalized_to_engine_observation,
)
from data_quality.models import QualityStatus as DQQualityStatus
from data_quality.pipeline import run_pipeline as run_dq_pipeline
from statistical_engine.core.comparability import match_comparable_pairs
from statistical_engine.engine import AirfareStatisticalEngine
from statistical_engine.models.index_result import CalculationStatus
from statistical_engine.models.observation import (
    BookingWindow as SEBookingWindow,
    FareObservation as EngineFareObservation,
    QualityStatus as SEQualityStatus,
)
from statistical_engine.models.weights import get_demo_reference_weights


@pytest.fixture()
def db_session():
    """Isolated in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def create_realistic_ignav_records(
    observation_date: date,
    price_multiplier: float = 1.0,
    include_duplicate: bool = False,
    routes: Optional[List[Tuple[str, str]]] = None,
) -> List[RawFareRecord]:
    """Create realistic IGNAV flight records resembling live API payloads."""
    target_routes = routes or [("DEL", "BOM"), ("BOM", "DEL"), ("DEL", "BLR"), ("BLR", "DEL"), ("BOM", "BLR"), ("BLR", "BOM")]
    records: List[RawFareRecord] = []
    now = datetime.now(timezone.utc)

    flight_schedules = [
        ("6E 5021", "IndiGo", dtime(6, 0), 5200.0),
        ("6E 2134", "IndiGo", dtime(8, 45), 5400.0),
        ("AI 804", "Air India", dtime(10, 30), 6100.0),
        ("AI 506", "Air India", dtime(14, 15), 6300.0),
        ("QP 1102", "Akasa Air", dtime(16, 30), 4800.0),
        ("UK 812", "Vistara", dtime(19, 45), 5900.0),
    ]

    for orig, dest in target_routes:
        for lead_days in [1, 7, 15, 30, 45]:
            travel_d = observation_date + timedelta(days=lead_days)
            for flight_no, airline, dep_time, base_fare in flight_schedules:
                fare = round(base_fare * price_multiplier, 2)
                rec = RawFareRecord(
                    origin=orig,
                    destination=dest,
                    travel_date=travel_d,
                    observation_date=observation_date,
                    booking_window=lead_days,
                    airline=airline,
                    flight_number=flight_no,
                    departure_time=dep_time,
                    cabin_class="ECONOMY",
                    fare_type="SAVER",
                    baggage_characteristics="15KG",
                    fare_amount=fare,
                    currency="INR",
                    source="IGNAV",
                    observation_timestamp=now,
                    metadata={"live_test": True},
                )
                records.append(rec)

    if include_duplicate and records:
        # Add an exact duplicate of the first record to verify DQ excludes it
        first = records[0]
        records.append(
            RawFareRecord(
                origin=first.origin,
                destination=first.destination,
                travel_date=first.travel_date,
                observation_date=first.observation_date,
                booking_window=first.booking_window,
                airline=first.airline,
                flight_number=first.flight_number,
                departure_time=first.departure_time,
                cabin_class=first.cabin_class,
                fare_type=first.fare_type,
                baggage_characteristics=first.baggage_characteristics,
                fare_amount=first.fare_amount,
                currency=first.currency,
                source=first.source,
                observation_timestamp=first.observation_timestamp,
                metadata={"duplicate": True},
            )
        )

    return records


class MockLiveIgnavAdapter:
    """Mock IGNAV live adapter tracking collection calls for testing."""

    def __init__(self, multiplier_by_date: Optional[Dict[date, float]] = None, include_duplicate: bool = False):
        self.calls: List[date] = []
        self.multiplier_by_date = multiplier_by_date or {}
        self.include_duplicate = include_duplicate

    def get_status(self) -> SourceStatus:
        return SourceStatus.AVAILABLE

    def collect_all(
        self,
        observation_date: Optional[date] = None,
        routes: Optional[List[Tuple[str, str]]] = None,
        booking_windows: Optional[List[int]] = None,
    ) -> List[RawFareRecord]:
        obs_d = observation_date or date.today()
        self.calls.append(obs_d)
        mult = self.multiplier_by_date.get(obs_d, 1.0)
        return create_realistic_ignav_records(
            observation_date=obs_d,
            price_multiplier=mult,
            include_duplicate=self.include_duplicate,
            routes=routes,
        )


# ==============================================================================
# TEST A: Two-Period Live Pairing Test
# ==============================================================================
def test_two_period_live_pairing_success():
    """Verify that real-shaped observations for consecutive dates have >0 comparable
    fingerprints and produce CalculationStatus.SUCCESS from the frozen Statistical Engine.
    """
    prev_date = date(2026, 9, 16)
    curr_date = date(2026, 9, 17)

    # 1. Generate real-shaped records for BLR-DEL route with consecutive dates
    raw_prev = create_realistic_ignav_records(prev_date, price_multiplier=1.0, routes=[("BLR", "DEL")])
    raw_curr = create_realistic_ignav_records(curr_date, price_multiplier=1.02, routes=[("BLR", "DEL")])

    dq_prev = run_dq_pipeline(raw_prev)
    dq_curr = run_dq_pipeline(raw_curr)

    obs_prev: List[EngineFareObservation] = [
        normalized_to_engine_observation(n)
        for n in dq_prev.normalized_observations
        if n.quality_status == DQQualityStatus.VALID and normalized_to_engine_observation(n)
    ]
    obs_curr: List[EngineFareObservation] = [
        normalized_to_engine_observation(n)
        for n in dq_curr.normalized_observations
        if n.quality_status == DQQualityStatus.VALID and normalized_to_engine_observation(n)
    ]

    assert len(obs_prev) > 0
    assert len(obs_curr) > 0

    # Filter to T+7 window
    t7_prev = [o for o in obs_prev if o.booking_window == SEBookingWindow.T_7]
    t7_curr = [o for o in obs_curr if o.booking_window == SEBookingWindow.T_7]

    # 2. Check comparable matched pairs
    pairing_res = match_comparable_pairs(t7_curr, t7_prev)
    assert len(pairing_res.matched_pairs) > 0, "Must have >0 comparable matched pairs across consecutive live dates"
    assert len(pairing_res.matched_pairs) == len(t7_curr) == 6

    # 3. Frozen Statistical Engine calculation
    engine = AirfareStatisticalEngine(allow_partial_coverage=True)
    weights = get_demo_reference_weights()
    calc = engine.calculate_daily_indices(
        current_observations=obs_curr,
        previous_observations=obs_prev,
        observation_date=curr_date,
        previous_observation_date=prev_date,
        weight_config=weights,
    )

    route_res = calc.route_results["BLR-DEL"]
    t7_res = route_res.window_indices[SEBookingWindow.T_7]
    assert t7_res.status == CalculationStatus.SUCCESS
    assert t7_res.index_value is not None
    assert round(t7_res.index_value, 2) == 102.00  # 2% price increase applied
    assert t7_res.num_matched_pairs == 6
    assert not t7_res.warnings


# ==============================================================================
# TEST B: Cold-Start Integration Test
# ==============================================================================
def test_cold_start_live_collection_and_persistence(db_session):
    """Verify cold-start behavior when DB has no previous IGNAV observations:
    - Both previous and current observation dates are collected.
    - Non-EXCLUDED records for both dates persist into fare_observations.
    - Duplicate EXCLUDED records are skipped (preserving unique constraint).
    - Statistical Engine returns SUCCESS with numeric indices.
    """
    curr_date = date(2026, 9, 17)
    prev_date = date(2026, 9, 16)

    # Confirm DB is completely empty of IGNAV observations
    ignav_count_before = (
        db_session.query(DBFareObservation)
        .filter(DBFareObservation.source == "IGNAV")
        .count()
    )
    assert ignav_count_before == 0

    mock_adapter = MockLiveIgnavAdapter(
        multiplier_by_date={prev_date: 1.0, curr_date: 1.03},
        include_duplicate=True,  # Test duplicate handling during live crawl
    )

    result = run_pipeline(
        db=db_session,
        target_date=curr_date,
        use_live_source=True,
        live_adapter=mock_adapter,
        clean=True,
    )

    # 1. Pipeline result checks
    assert result["status"] == "SUCCESS"
    assert result["mode"] == "LIVE"
    assert result["cold_start"] is True
    assert result["observation_date"] == curr_date.isoformat()
    assert result["previous_observation_date"] == prev_date.isoformat()

    # 2. Both previous and current dates collected via adapter
    assert prev_date in mock_adapter.calls
    assert curr_date in mock_adapter.calls
    assert len(mock_adapter.calls) == 2

    # 3. Both dates persisted to DB
    obs_prev_count = (
        db_session.query(DBFareObservation)
        .filter(
            DBFareObservation.source == "IGNAV",
            DBFareObservation.observation_date == prev_date,
        )
        .count()
    )
    obs_curr_count = (
        db_session.query(DBFareObservation)
        .filter(
            DBFareObservation.source == "IGNAV",
            DBFareObservation.observation_date == curr_date,
        )
        .count()
    )
    assert obs_prev_count > 0, "Previous date observations must be persisted"
    assert obs_curr_count > 0, "Current date observations must be persisted"

    # 4. EXCLUDED records were NOT inserted (Requirement E)
    excluded_count = (
        db_session.query(DBFareObservation)
        .filter(DBFareObservation.quality_status == "EXCLUDED")
        .count()
    )
    assert excluded_count == 0, "EXCLUDED records must not be in fare_observations"

    # 5. National indices are numeric
    nat_indices = result["national_indices"]
    assert "T+7" in nat_indices
    assert float(nat_indices["T+7"]) > 0
    assert abs(float(nat_indices["T+7"]) - 103.0) < 0.1

    # 6. Index results stored in DB
    idx_records = (
        db_session.query(DBIndexResult)
        .filter(DBIndexResult.observation_date == curr_date)
        .all()
    )
    assert len(idx_records) == 5
    for idx_rec in idx_records:
        assert idx_rec.status == "SUCCESS"
        assert idx_rec.index_value is not None


# ==============================================================================
# TEST C: Incremental Integration Test
# ==============================================================================
def test_incremental_live_loading_from_db(db_session):
    """Verify incremental behavior when DB already contains previous IGNAV observations:
    - Previous date observations are loaded directly from DB.
    - Adapter collect_all is NOT called for prev_date.
    - Adapter collect_all IS called for curr_date.
    - Indices are computed successfully between DB-loaded prev and newly collected curr.
    """
    day1 = date(2026, 9, 16)
    day2 = date(2026, 9, 17)
    day3 = date(2026, 9, 18)

    # 1. Run day2 (which cold-starts day1 + day2 into DB)
    adapter_run1 = MockLiveIgnavAdapter(
        multiplier_by_date={day1: 1.0, day2: 1.02},
    )
    res1 = run_pipeline(
        db=db_session,
        target_date=day2,
        use_live_source=True,
        live_adapter=adapter_run1,
        clean=False,
    )
    assert res1["status"] == "SUCCESS"
    assert res1["cold_start"] is True
    assert set(adapter_run1.calls) == {day1, day2}

    # Verify day2 observations are in DB
    day2_obs_count = (
        db_session.query(DBFareObservation)
        .filter(
            DBFareObservation.source == "IGNAV",
            DBFareObservation.observation_date == day2,
            DBFareObservation.quality_status != "EXCLUDED",
        )
        .count()
    )
    assert day2_obs_count > 0

    # 2. Run day3 incrementally (target_date=day3, prev_date=day2)
    adapter_run2 = MockLiveIgnavAdapter(
        multiplier_by_date={day3: 1.05},
    )
    res2 = run_pipeline(
        db=db_session,
        target_date=day3,
        use_live_source=True,
        live_adapter=adapter_run2,
        clean=False,
    )

    # 3. Assertions for incremental run
    assert res2["status"] == "SUCCESS"
    assert res2["mode"] == "LIVE"
    assert res2["cold_start"] is False, "Must NOT be cold start when prev_date exists in DB"
    assert res2["previous_observation_date"] == day2.isoformat()
    assert res2["observation_date"] == day3.isoformat()

    # Verify adapter was called ONLY for day3, NOT for day2!
    assert day3 in adapter_run2.calls
    assert day2 not in adapter_run2.calls, "Previous date must NOT be recollected when already in DB"
    assert len(adapter_run2.calls) == 1

    # Verify day3 observations are now in DB
    day3_obs_count = (
        db_session.query(DBFareObservation)
        .filter(
            DBFareObservation.source == "IGNAV",
            DBFareObservation.observation_date == day3,
        )
        .count()
    )
    assert day3_obs_count > 0

    # Verify national index is numeric and computed relative to day2
    nat_indices = res2["national_indices"]
    assert "T+7" in nat_indices
    assert float(nat_indices["T+7"]) > 0


# ==============================================================================
# TEST E: Database Integrity & Conversion Helper Test
# ==============================================================================
def test_db_obs_to_engine_obs_conversion(db_session):
    """Verify that db_obs_to_engine_obs cleanly parses all DB observation fields."""
    route = DBRoute(code="DEL-BOM", origin="DEL", destination="BOM")
    db_session.add(route)
    db_session.flush()

    obs = DBFareObservation(
        route_id=route.id,
        observation_timestamp=datetime.now(timezone.utc),
        observation_date=date(2026, 9, 17),
        travel_date=date(2026, 9, 24),
        booking_window="T+7",
        airline="INDIGO",
        flight_number="6E-5021",
        departure_time="06:00",
        cabin_class="ECONOMY",
        fare_type="SAVER",
        baggage_characteristics="15KG",
        base_fare=Decimal("4500.00"),
        taxes=Decimal("700.00"),
        mandatory_charges=Decimal("0.00"),
        comparable_fare=Decimal("5200.00"),
        source="IGNAV",
        fingerprint="test_fingerprint_abc",
        quality_status="VALID",
        metadata_json={"test": True},
    )
    db_session.add(obs)
    db_session.commit()

    engine_obs = db_obs_to_engine_obs(obs)
    assert engine_obs is not None
    assert engine_obs.origin == "DEL"
    assert engine_obs.destination == "BOM"
    assert engine_obs.booking_window == SEBookingWindow.T_7
    assert engine_obs.comparable_fare == 5200.0
    assert engine_obs.quality_status == SEQualityStatus.VALID
    assert engine_obs.airline == "INDIGO"
    assert engine_obs.flight_number == "6E-5021"
    assert engine_obs.departure_time == "06:00"
