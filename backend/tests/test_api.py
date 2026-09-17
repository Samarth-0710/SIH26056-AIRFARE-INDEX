def store_index(client, payload):
    return client.post("/api/v1/ingestion/index-results", json={"payload": payload, "route_indices": [{
        "route": "DEL-BOM", "index_value": "102.0", "status": "SUCCESS", "weight": "0.1", "contribution": "10.2"
    }]})


def test_system_endpoints(client):
    assert client.get("/").json() == {"message": "SIH26056 Airfare Price Index API", "status": "running"}
    assert client.get("/health").json() == {"status": "healthy"}
    assert client.get("/docs").status_code == 200


def test_empty_official_index_returns_not_found(client):
    assert client.get("/api/v1/index/current").status_code == 404


def test_index_route_and_booking_window_apis(client, index_payload):
    assert store_index(client, index_payload).status_code == 201
    current = client.get("/api/v1/index/current?booking_window=T%2B7")
    assert current.status_code == 200 and float(current.json()["index"]) == 101.5
    assert len(client.get("/api/v1/index/history").json()["items"]) == 1
    assert client.get("/api/v1/routes").json()[0]["route"] == "DEL-BOM"
    assert client.get("/api/v1/routes/DEL-BOM/index").status_code == 200
    assert client.get("/api/v1/booking-windows").json() == ["T+1", "T+7", "T+15", "T+30", "T+45"]
    assert client.get("/api/v1/booking-windows/T%2B7/index").status_code == 200


def test_immutable_result_and_validation(client, index_payload):
    assert store_index(client, index_payload).status_code == 201
    assert store_index(client, index_payload).status_code == 409
    assert client.get("/api/v1/routes/not-a-route/index").status_code == 422
    assert client.get("/api/v1/index/history?start=2026-09-02&end=2026-09-01").status_code == 422


def test_quality_intelligence_shocks_and_simulation(client, index_payload):
    assert client.post("/api/v1/ingestion/quality", json={"metric_date":"2026-09-01", "observation_count":10,
        "status":"COMPLETE", "generated_at":"2026-09-01T12:00:00Z"}).status_code == 201
    assert len(client.get("/api/v1/quality").json()) == 1
    assert client.post("/api/v1/ingestion/intelligence", json={"route":"DEL-BOM", "event_type":"SHOCK",
        "shock_status":"ALERT", "model_version":"MODEL_TEST", "event_timestamp":"2026-09-01T12:00:00Z"}).status_code == 201
    assert len(client.get("/api/v1/intelligence").json()) == 1
    assert len(client.get("/api/v1/intelligence/shocks").json()) == 1
    assert store_index(client, index_payload).status_code == 201
    simulation = client.post("/api/v1/simulation", json={"route":"DEL-BOM", "shock_percent":15, "projected_index":105})
    assert simulation.status_code == 201 and simulation.json()["simulation"] is True


def test_simulation_never_invents_projection(client):
    response = client.post("/api/v1/simulation", json={"route":"DEL-BOM", "shock_percent":15})
    assert response.status_code in (404, 409)


def test_new_analytical_endpoints(client, index_payload):
    assert store_index(client, index_payload).status_code == 201

    # Test route contributions endpoint
    contrib = client.get("/api/v1/routes/contributions")
    assert contrib.status_code == 200
    data = contrib.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "route" in data[0]
        assert "level_contribution" in data[0]

    # Test booking windows matrix endpoint
    matrix = client.get("/api/v1/booking-windows/matrix")
    assert matrix.status_code == 200
    assert isinstance(matrix.json(), list)

    # Test quality summary endpoint
    qual_summary = client.get("/api/v1/quality/summary")
    assert qual_summary.status_code == 200
    assert "total_observations" in qual_summary.json()
    assert "source_health" in qual_summary.json()

    # Test validation endpoint
    val = client.get("/api/v1/validation")
    assert val.status_code == 200
    val_json = val.json()
    assert "is_reference_connected" in val_json
    assert "metrics" in val_json
    assert "history" in val_json
    assert isinstance(val_json["metrics"], list)


def test_pipeline_live_status_endpoint_states(client):
    from unittest.mock import patch
    from data_collection.adapters import SourceStatus

    # 1. Connected state
    with patch("data_collection.ignav_adapter.IgnavFareAdapter.check_connection", return_value=(SourceStatus.AVAILABLE, "Live Ignav airfare data is available.")):
        with patch.object(client.app, "state", create=True):
            resp = client.get("/api/v1/pipeline/live-status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["source"] == "IGNAV"
            assert data["is_configured"] is True
            assert data["is_connected"] is True
            assert data["status"] == "CONNECTED"
            assert "Live Ignav airfare data is available" in data["message"]
            assert "api_key" not in data
            assert "key" not in data

    # 2. Missing credentials state
    with patch("data_collection.ignav_adapter.IgnavFareAdapter.__init__", lambda self, **kwargs: setattr(self, "api_key", None)):
        resp = client.get("/api/v1/pipeline/live-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "IGNAV"
        assert data["is_configured"] is False
        assert data["is_connected"] is False
        assert data["status"] == "NOT_CONFIGURED"
        assert "unconfigured" in data["message"]
        assert "api_key" not in data

    # 3. Degraded / Unreachable state
    with patch("data_collection.ignav_adapter.IgnavFareAdapter.check_connection", return_value=(SourceStatus.DEGRADED, "Live Ignav API unreachable (Timeout); synthetic fallback active.")):
        with patch("data_collection.ignav_adapter.IgnavFareAdapter.__init__", lambda self, **kwargs: setattr(self, "api_key", "mock_key")):
            resp = client.get("/api/v1/pipeline/live-status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["source"] == "IGNAV"
            assert data["is_configured"] is True
            assert data["is_connected"] is False
            assert data["status"] == "DEGRADED"
            assert "unreachable" in data["message"].lower() or "fallback" in data["message"].lower()
            assert "mock_key" not in str(data)
