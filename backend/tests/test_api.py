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
