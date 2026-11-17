def test_health_ok(anon_client):
    r = anon_client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
