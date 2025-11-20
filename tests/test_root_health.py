"""
Tests for health and readiness endpoints.
"""

# The client fixture is automatically imported from tests/conftest.py
# No need for sys.path manipulation or local client fixtures here.


def test_health_endpoint(client):
    """
    Tests the /health endpoint for a basic 'healthy' response.
    """
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "timestamp" in body
    assert body["version"] == "2.0.0"


def test_readiness_check_success(client, mock_db_manager):
    """
    Tests the /ready endpoint when the database is healthy.
    """
    # The mock_db_manager from conftest already mocks check_health to return success
    mock_db_manager.check_health.return_value = {"status": "ok"}

    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"]["status"] == "ok"


def test_readiness_check_failure(client, mock_db_manager):
    """
    Tests the /ready endpoint when the database is not healthy.
    """
    # Override the mock to simulate a failure
    mock_db_manager.check_health.return_value = {
        "status": "error",
        "error": "Connection failed",
    }

    response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["detail"] == "Database not ready: Connection failed"
