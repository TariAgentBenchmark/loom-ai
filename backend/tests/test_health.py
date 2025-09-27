from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_message() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "LoomAI backend is up"}
