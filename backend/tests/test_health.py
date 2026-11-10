from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_root_returns_metadata() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "0.2.0"
