import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AlphaStrat Trading Platform API"
    assert "version" in data


def test_health_endpoint(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data


@pytest.mark.asyncio
async def test_scanner_status(client: TestClient):
    """Test scanner status endpoint."""
    response = client.get("/api/v1/scanner/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "opportunities_found_today" in data