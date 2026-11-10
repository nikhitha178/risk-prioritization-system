
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_dashboard():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "total_alerts" in data
    assert "total_cases" in data


def test_cases():
    response = client.get("/api/cases")
    assert response.status_code == 200
    assert response.json() is not None


def test_alerts():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    assert response.json() is not None


def test_analysts():
    response = client.get("/api/analysts")
    assert response.status_code == 200
    assert response.json() is not None


def test_case_details():
    response = client.get("/api/cases/CASE-2026-000001")
    assert response.status_code == 200
    assert response.json()["case_id"] == "CASE-2026-000001"
