from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import (
    FareObservation,
    IndexResult,
    MoSPIAirfareReference,
    RouteIndex,
)
from app.services.pipeline_service import load_mospi_reference_dataset
from app.services.validation_service import get_validation_analysis


def _find_reference_excel() -> Path:
    candidates = [
        Path("data/reference/CPI_Airfare.xlsx"),
        Path(__file__).resolve().parents[2] / "data" / "reference" / "CPI_Airfare.xlsx",
        Path("../data/reference/CPI_Airfare.xlsx"),
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    return candidates[0]


EXCEL_PATH = _find_reference_excel()


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_mospi_reference_loading_and_idempotence(db_session):
    assert EXCEL_PATH.exists()

    # Initial load: 20 records
    count1 = load_mospi_reference_dataset(db_session, EXCEL_PATH)
    assert count1 == 20

    records = db_session.query(MoSPIAirfareReference).order_by(MoSPIAirfareReference.reference_date.asc()).all()
    assert len(records) == 20

    first = records[0]
    latest = records[-1]
    assert first.reference_date == date(2025, 1, 1)
    assert float(first.index_value) == pytest.approx(115.05, abs=0.01)
    assert latest.reference_date == date(2026, 8, 1)
    assert float(latest.index_value) == pytest.approx(135.49, abs=0.01)

    # Re-running load must be idempotent (0 new, total stays 20)
    count2 = load_mospi_reference_dataset(db_session, EXCEL_PATH)
    assert count2 == 0
    assert db_session.query(MoSPIAirfareReference).count() == 20


def test_mospi_database_isolation(db_session):
    # Load MoSPI reference
    load_mospi_reference_dataset(db_session, EXCEL_PATH)

    # Statistical engine and fare tables must remain untouched
    assert db_session.query(FareObservation).count() == 0
    assert db_session.query(IndexResult).count() == 0
    assert db_session.query(RouteIndex).count() == 0


def test_validation_endpoint_disconnected(client):
    # Test client starts with empty DB (no MoSPI loaded)
    resp = client.get("/api/v1/validation")
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_reference_connected"] is False
    assert data["reference_dataset_details"]["connected"] is False
    assert data["reference_dataset_details"]["records"] == 0
    assert data["alignment"]["status"] in ("NOT_CONNECTED", "NO_OVERLAP")


def test_validation_metrics_and_endpoint_connected(client):
    from app.db.database import get_db
    override_gen = client.app.dependency_overrides[get_db]()
    db = next(override_gen)
    try:
        load_mospi_reference_dataset(db, EXCEL_PATH)
    finally:
        try:
            next(override_gen)
        except StopIteration:
            pass

    # Now query /api/v1/validation
    resp = client.get("/api/v1/validation")
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_reference_connected"] is True
    ref = data["reference_dataset_details"]
    assert ref["connected"] is True
    assert ref["records"] == 20
    assert ref["item_code"] == "07.3.3.1.2.01"
    assert ref["base_year"] == 2024
    assert ref["state"] == "All India"
    assert ref["sector"] == "Combined"
    assert ref["latest_cpi"] == pytest.approx(135.49, abs=0.01)

    # Check monthly series
    mospi_points = [p for p in data["monthly_series"] if p["mospi_cpi"] is not None]
    assert len(mospi_points) == 20


def test_validation_aggregation_and_rebasing(db_session):
    from datetime import datetime, timezone
    now_ts = datetime.now(timezone.utc)
    load_mospi_reference_dataset(db_session, EXCEL_PATH)

    # Insert synthetic T+15 daily index results for August 2026 and September 2026
    # August 2026: 2 days (105.0, 107.0 -> mean 106.0)
    for day, val in [(15, Decimal("105.0")), (20, Decimal("107.0"))]:
        db_session.add(IndexResult(
            observation_date=date(2026, 8, day),
            booking_window="T+15",
            index_value=val,
            status="SUCCESS",
            observation_set_version="v1",
            basket_version="v1",
            weight_version="v1",
            methodology_version="Jevons",
            calculation_version="v1",
            execution_checksum=f"chk_8_{day}",
            calculation_timestamp=now_ts,
        ))

    # September 2026: 1 day (110.0)
    db_session.add(IndexResult(
        observation_date=date(2026, 9, 1),
        booking_window="T+15",
        index_value=Decimal("110.0"),
        status="SUCCESS",
        observation_set_version="v1",
        basket_version="v1",
        weight_version="v1",
        methodology_version="Jevons",
        calculation_version="v1",
        execution_checksum="chk_9_1",
        calculation_timestamp=now_ts,
    ))
    db_session.commit()

    val_result = get_validation_analysis(db_session)
    assert val_result.is_reference_connected is True
    assert val_result.alignment.overlapping_months == 1
    assert "2026-08" in val_result.alignment.aligned_months

    # Check comparison on overlapping month 2026-08
    comp = val_result.comparison
    assert comp.reference_month == "2026-08"
    assert comp.our_monthly_index == pytest.approx(106.0, abs=0.01)
    assert comp.mospi_monthly_index == pytest.approx(135.49, abs=0.01)
    # Rebasing to 2026-08: both rebased indices should be 100.0
    assert comp.our_rebased_index == pytest.approx(100.0, abs=0.01)
    assert comp.mospi_rebased_index == pytest.approx(100.0, abs=0.01)

    # Check terminology: when overlapping_months == 1, metric must be Absolute Level Difference
    metric_names = [m.metric for m in val_result.metrics]
    assert "Absolute Level Difference" in metric_names
    assert "Mean Absolute Error (MAE)" not in metric_names


def test_daily_to_monthly_aggregation_mathematics(db_session):
    from datetime import datetime, timezone
    now_ts = datetime.now(timezone.utc)

    # Month 1 (August 2026): Days 10 (100.0), 20 (110.0), 31 (120.0)
    # Expected August mean: (100.0 + 110.0 + 120.0) / 3 = 110.0
    for day, val in [(10, Decimal("100.0")), (20, Decimal("110.0")), (31, Decimal("120.0"))]:
        db_session.add(IndexResult(
            observation_date=date(2026, 8, day),
            booking_window="T+15",
            index_value=val,
            status="SUCCESS",
            observation_set_version="v1",
            basket_version="v1",
            weight_version="v1",
            methodology_version="Jevons",
            calculation_version="v1",
            execution_checksum=f"chk_8_{day}",
            calculation_timestamp=now_ts,
        ))

    # Month 2 (September 2026): Days 1 (130.0), 15 (140.0)
    # Missing days in between must not affect arithmetic mean of observed days
    # Expected September mean: (130.0 + 140.0) / 2 = 135.0
    for day, val in [(1, Decimal("130.0")), (15, Decimal("140.0"))]:
        db_session.add(IndexResult(
            observation_date=date(2026, 9, day),
            booking_window="T+15",
            index_value=val,
            status="SUCCESS",
            observation_set_version="v1",
            basket_version="v1",
            weight_version="v1",
            methodology_version="Jevons",
            calculation_version="v1",
            execution_checksum=f"chk_9_{day}",
            calculation_timestamp=now_ts,
        ))
    db_session.commit()

    val_res = get_validation_analysis(db_session)
    monthly_map = {p.month: p.our_monthly_index for p in val_res.monthly_series if p.our_monthly_index is not None}

    # Verify strict month boundary separation & arithmetic mean values
    assert monthly_map["2026-08"] == pytest.approx(110.0, abs=1e-4)
    assert monthly_map["2026-09"] == pytest.approx(135.0, abs=1e-4)
    assert len(monthly_map) == 2


def test_simulator_safety_does_not_mutate_official_index(client, index_payload):
    from backend.tests.test_api import store_index
    # Store official index result
    resp = store_index(client, index_payload)
    assert resp.status_code == 201

    # 1. Fetch official index before simulation
    curr_before = client.get("/api/v1/index/current?booking_window=T%2B7")
    assert curr_before.status_code == 200
    val_before = float(curr_before.json()["index"])
    hist_before = client.get("/api/v1/index/history").json()["items"]

    # 2. Run simulation with large shock
    sim_resp = client.post("/api/v1/simulation", json={"route": "DEL-BOM", "shock_percent": 25.0, "projected_index": 125.0})
    assert sim_resp.status_code == 201
    assert sim_resp.json()["simulation"] is True

    # 3. Fetch official index after simulation
    curr_after = client.get("/api/v1/index/current?booking_window=T%2B7")
    assert curr_after.status_code == 200
    val_after = float(curr_after.json()["index"])
    hist_after = client.get("/api/v1/index/history").json()["items"]

    # 4. Assert official index is completely unchanged
    assert val_before == val_after
    assert len(hist_before) == len(hist_after)
    assert hist_before[0]["index"] == hist_after[0]["index"]
