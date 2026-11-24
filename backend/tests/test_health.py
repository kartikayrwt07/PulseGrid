def test_health_get(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["db_ok"] is True
    assert body["model_loaded"] is True
    assert body["dataset_count"] == 240


def test_health_head(client):
    res = client.head("/api/v1/health")
    assert res.status_code == 200
