import os
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    def override_db():
        db = TestingSession()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def index_payload():
    return {
        "observation_date": "2026-09-01", "booking_window": "T+7", "index_value": "101.5", "status": "SUCCESS",
        "observation_set_version": "OBS_TEST", "basket_version": "BASKET_TEST", "weight_version": "WEIGHTS_TEST",
        "methodology_version": "JEVONS_TEST", "calculation_version": "CALC_TEST_1", "execution_checksum": "test-checksum",
        "calculation_timestamp": "2026-09-01T12:00:00Z"
    }
