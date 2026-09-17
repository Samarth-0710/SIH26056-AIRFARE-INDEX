"""Comprehensive Integration Test Suite for SIH26056 Airfare Price Index.

Tests all seven critical integration boundaries:
TEST 1: Data Collection -> Data Quality
TEST 2: Data Quality -> Statistical Engine
TEST 3: Statistical Engine -> Intelligence
TEST 4: Complete Pipeline -> Database Persistence
TEST 5: Backend API -> Database Retrieval
TEST 6: What-If Simulator calculation and projection
TEST 7: Full end-to-end flow (Collection -> Quality -> Engine -> Intelligence -> DB -> API)
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import (
    FareObservation as DBFareObservation,
    IndexResult as DBIndexResult,
    IntelligenceEvent as DBIntelligenceEvent,
    QualityMetric as DBQualityMetric,
    Route as DBRoute,
    RouteIndex as DBRouteIndex,
    SimulationResult as DBSimulationResult,
)
from app.main import app
from app.services.pipeline_service import generate_synthetic_records, run_pipeline
from data_collection.mock_adapter import MockFareAdapter
from data_collection.models import RawFareRecord
from data_quality.bridge import (
    clean_and_convert_records,
    normalized_to_engine_observation,
    raw_record_to_raw_observation,
)
from data_quality.models import BookingWindow as DQBookingWindow, QualityStatus as DQQualityStatus
from data_quality.pipeline import run_pipeline as run_dq_pipeline
from intelligence.integration.statistical_engine_adapter import (
    StatisticalEngineIntelligenceAdapter,
)
from intelligence.models.result import IntelligenceStatus
from statistical_engine.engine import AirfareStatisticalEngine
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


@pytest.fixture()
def test_client(db_session):
    """FastAPI TestClient with overridden database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ==============================================================================
# TEST 1: Data Collection -> Data Quality
# ==============================================================================
def test_boundary_1_collection_to_quality():
    """Verify that records collected by data-collection can be converted and
    processed by the data-quality module without loss or corruption.
    """
    adapter = MockFareAdapter()
    raw_records = adapter.collect_all_windows(origin="DEL", destination="BOM")
    assert len(raw_records) == 5

    # Convert RawFareRecord -> RawFareObservation
    raw_observations = [raw_record_to_raw_observation(r) for r in raw_records]
    assert len(raw_observations) == 5
    for obs in raw_observations:
        assert obs.origin == "DEL"
        assert obs.destination == "BOM"
        assert obs.source == "mock"
        assert obs.total_fare == 5400.0
        assert obs.base_fare is not None
        assert obs.taxes is not None
        assert obs.departure_time == "07:30"
        assert obs.booking_window in ["T+1", "T+7", "T+15", "T+30", "T+45"]

    # Run through data quality pipeline
    dq_result = run_dq_pipeline(raw_observations)
    assert dq_result.total_processed == 5
    assert len(dq_result.rejected_observations) == 0
    assert len(dq_result.normalized_observations) == 5

    for norm in dq_result.normalized_observations:
        assert norm.quality_status == DQQualityStatus.VALID
        assert norm.comparable_fare == 5400.0
        assert norm.fingerprint is not None
        assert len(norm.fingerprint) > 10


# ==============================================================================
# TEST 2: Data Quality -> Statistical Engine
# ==============================================================================
def test_boundary_2_quality_to_statistical_engine():
    """Verify that NormalizedFareObservations convert cleanly to
    statistical engine FareObservations and produce valid Jevons indices.
    """
    today = date(2026, 9, 2)
    yesterday = date(2026, 9, 1)

    adapter = MockFareAdapter()
    records_prev = adapter.collect_all_windows("DEL", "BOM", observation_date=yesterday)
    records_curr = adapter.collect_all_windows("DEL", "BOM", observation_date=today)

    # Apply 10% price increase on day t
    for r in records_curr:
        r.fare_amount = r.fare_amount * 1.10

    obs_prev = clean_and_convert_records(records_prev)
    obs_curr = clean_and_convert_records(records_curr)

    assert len(obs_prev) == 5
    assert len(obs_curr) == 5

    for o in obs_curr:
        assert isinstance(o, EngineFareObservation)
        assert o.quality_status == SEQualityStatus.VALID
        assert round(o.comparable_fare, 2) == 5940.0

    engine = AirfareStatisticalEngine(allow_partial_coverage=True)
    calc = engine.calculate_daily_indices(
        current_observations=obs_curr,
        previous_observations=obs_prev,
        observation_date=today,
        previous_observation_date=yesterday,
    )

    # Route DEL-BOM must have an index of exactly 110.0 across all windows
    route_res = calc.route_results["DEL-BOM"]
    for bw in SEBookingWindow:
        win_idx = route_res.window_indices[bw]
        assert win_idx.status.value == "SUCCESS"
        assert abs(win_idx.index_value - 110.0) < 1e-4


# ==============================================================================
# TEST 3: Statistical Engine -> Intelligence
# ==============================================================================
def test_boundary_3_statistical_engine_to_intelligence():
    """Verify that Statistical Engine outputs are correctly consumed by the
    Intelligence adapter to detect anomalies, shocks, and explanations.
    """
    today = date(2026, 9, 2)
    yesterday = date(2026, 9, 1)

    records_prev = generate_synthetic_records(yesterday, price_factor=1.0)
    records_curr = generate_synthetic_records(today, price_factor=1.15)  # 15% shock

    obs_prev = clean_and_convert_records(records_prev)
    obs_curr = clean_and_convert_records(records_curr)

    engine = AirfareStatisticalEngine(allow_partial_coverage=True)
    engine_output = engine.calculate_daily_indices(
        current_observations=obs_curr,
        previous_observations=obs_prev,
        observation_date=today,
        previous_observation_date=yesterday,
    )

    adapter = StatisticalEngineIntelligenceAdapter()
    intel_by_window = adapter.analyze_windows(engine_output)

    assert len(intel_by_window) == 5
    for bw, intel_out in intel_by_window.items():
        assert intel_out.status == IntelligenceStatus.SUCCESS
        assert len(intel_out.anomalies) > 0
        for anomaly in intel_out.anomalies:
            assert anomaly.route is not None
            assert anomaly.current_index is not None


# ==============================================================================
# TEST 4: Complete Pipeline -> Database Persistence
# ==============================================================================
def test_boundary_4_pipeline_to_database(db_session):
    """Verify that run_pipeline executes the full multi-day pipeline and writes to all tables."""
    target_d = date(2026, 9, 10)
    result = run_pipeline(db=db_session, target_date=target_d, price_movement_pct=3.0, days=30)

    assert result["status"] == "SUCCESS"
    assert result["observations_stored"] > 0
    assert result["index_results_stored"] >= 150
    assert result["route_indices_stored"] >= 900
    assert result["historical_days"] == 30

    # Verify rows in database
    routes_count = db_session.query(DBRoute).count()
    assert routes_count == 6

    obs_count = db_session.query(DBFareObservation).count()
    assert obs_count == result["observations_stored"]

    idx_count = db_session.query(DBIndexResult).count()
    assert idx_count == result["index_results_stored"]

    r_idx_count = db_session.query(DBRouteIndex).count()
    assert r_idx_count == result["route_indices_stored"]

    qm_count = db_session.query(DBQualityMetric).count()
    assert qm_count == result["quality_metrics_stored"]

    intel_count = db_session.query(DBIntelligenceEvent).count()
    assert intel_count == result["intelligence_events_stored"]
    assert intel_count > 0

    # Verify multi-day historical dates in index_results
    dates_cnt = db_session.query(DBIndexResult.observation_date).distinct().count()
    assert dates_cnt >= 30

    # Verify variation across booking windows (T+1 != T+7 != T+15 != T+30 != T+45)
    nat_indices = result["national_indices"]
    assert len(nat_indices) == 5
    assert nat_indices["T+1"] != nat_indices["T+15"]
    assert nat_indices["T+15"] != nat_indices["T+45"]
    assert all(val != 102.5 for val in nat_indices.values())


# ==============================================================================
# TEST 5: Backend API -> Database Retrieval
# ==============================================================================
def test_boundary_5_backend_api_retrieval(test_client, db_session):
    """Verify that once data is in the database, existing GET endpoints retrieve it."""
    target_d = date(2026, 9, 10)
    run_pipeline(db=db_session, target_date=target_d, price_movement_pct=2.0)

    # 1. GET /api/v1/index/current
    curr_res = test_client.get("/api/v1/index/current?booking_window=T%2B7")
    assert curr_res.status_code == 200
    curr_json = curr_res.json()
    assert curr_json["booking_window"] == "T+7"
    assert float(curr_json["index"]) > 0

    # 2. GET /api/v1/routes
    routes_res = test_client.get("/api/v1/routes")
    assert routes_res.status_code == 200
    assert len(routes_res.json()) == 6

    # 3. GET /api/v1/routes/DEL-BOM/index
    route_idx_res = test_client.get("/api/v1/routes/DEL-BOM/index?booking_window=T%2B7")
    assert route_idx_res.status_code == 200
    r_json = route_idx_res.json()
    assert r_json["route"] == "DEL-BOM"
    assert r_json["booking_window"] == "T+7"

    # 4. GET /api/v1/booking-windows
    bw_res = test_client.get("/api/v1/booking-windows")
    assert bw_res.status_code == 200
    assert bw_res.json() == ["T+1", "T+7", "T+15", "T+30", "T+45"]

    # 5. GET /api/v1/quality
    q_res = test_client.get("/api/v1/quality")
    assert q_res.status_code == 200
    assert len(q_res.json()) >= 1

    # 6. GET /api/v1/intelligence
    intel_res = test_client.get("/api/v1/intelligence")
    assert intel_res.status_code == 200
    assert len(intel_res.json()) >= 1


# ==============================================================================
# TEST 6: What-If Simulator
# ==============================================================================
def test_boundary_6_what_if_simulator(test_client, db_session):
    """Verify that What-If simulation works when frontend sends {route, shock_percent}."""
    # 1. When DB is empty, returns 409
    sim_empty = test_client.post("/api/v1/simulation", json={"route": "DEL-BOM", "shock_percent": 15})
    assert sim_empty.status_code in (404, 409)

    # 2. Seed DB with pipeline data
    run_pipeline(db=db_session, target_date=date(2026, 9, 10), price_movement_pct=0.0)

    # 3. Simulation without projected_index (Frontend shape)
    sim_res = test_client.post("/api/v1/simulation", json={"route": "DEL-BOM", "shock_percent": 10})
    assert sim_res.status_code == 201
    sim_data = sim_res.json()
    assert sim_data["simulation"] is True
    assert sim_data["route"] == "DEL-BOM"
    assert float(sim_data["shock_percent"]) == 10.0
    assert sim_data["projected_index"] is not None
    # DEL-BOM weight is 0.25; ~10% shock on current corridor index yields ~2.5 - 2.8 point impact
    assert float(sim_data["impact_points"]) > 0
    assert abs(float(sim_data["impact_points"]) - 2.6) < 0.5

    # 4. Simulation with pre-computed projected_index
    sim_pre = test_client.post(
        "/api/v1/simulation",
        json={"route": "DEL-BOM", "shock_percent": 15, "projected_index": 108.5},
    )
    assert sim_pre.status_code == 201
    assert float(sim_pre.json()["projected_index"]) == 108.5


# ==============================================================================
# TEST 7: Complete End-to-End Demo Flow
# ==============================================================================
def test_boundary_7_complete_end_to_end_flow(test_client):
    """Verify complete end-to-end demo flow triggered via API:
    POST /api/v1/pipeline/run
    -> data collection
    -> data quality
    -> statistical engine
    -> intelligence
    -> database
    -> GET API endpoints reflect live data
    """
    # Trigger pipeline run
    post_res = test_client.post(
        "/api/v1/pipeline/run",
        json={"price_movement_pct": 4.0},
    )
    assert post_res.status_code == 200
    run_data = post_res.json()
    assert run_data["status"] == "SUCCESS"
    assert "T+7" in run_data["national_indices"]

    # Check pipeline status endpoint
    status_res = test_client.get("/api/v1/pipeline/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "ACTIVE"

    # Verify that index/current returns the new index
    idx_res = test_client.get("/api/v1/index/current?booking_window=T%2B7")
    assert idx_res.status_code == 200
    assert float(idx_res.json()["index"]) > 100.0

    # Verify routes endpoint
    routes_res = test_client.get("/api/v1/routes")
    assert routes_res.status_code == 200
    routes_list = routes_res.json()
    assert len(routes_list) == 6

    # Verify simulator on live data
    sim_res = test_client.post("/api/v1/simulation", json={"route": "DEL-BLR", "shock_percent": 20})
    assert sim_res.status_code == 201
    assert sim_res.json()["projected_index"] is not None
