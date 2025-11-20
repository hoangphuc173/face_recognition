"""
Unit tests for the health check API endpoint, using FastAPI's dependency overrides.
"""

from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from aws.backend.api.routes import health
from aws.backend.utils.config import get_settings, Settings
from aws.backend.core.database_manager import DatabaseManager

# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(health.router)

# --- Mock Dependencies ---

def get_mock_settings():
    # Instantiate settings and then patch attributes
    settings = Settings()
    settings.app_env = "test"
    settings.db_path = "dummy/path"
    return settings

# Mock DatabaseManager class to control its instances
mock_db_manager_instance = MagicMock()
class MockDatabaseManager:
    def __init__(self, db_path: str):
        # We can assert this was called correctly
        assert db_path == "dummy/path"

    def get_all_people(self):
        return mock_db_manager_instance.get_all_people()

# --- Override Dependencies ---

app.dependency_overrides[get_settings] = get_mock_settings
# We need to override the class itself as it's instantiated inside the route
health.DatabaseManager = MockDatabaseManager

client = TestClient(app)


# --- Test Cases ---

def test_health_check_success():
    """Test the health check endpoint with successful dependency checks."""
    # Arrange
    mock_db_manager_instance.reset_mock()
    mock_db_manager_instance.get_all_people.return_value = [{"user_name": "test"}]
    mock_db_manager_instance.get_all_people.side_effect = None

    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_status"] == "healthy"
    mock_db_manager_instance.get_all_people.assert_called_once()


def test_health_check_db_error():
    """Test the health check endpoint when a dependency (Database) fails."""
    # Arrange
    mock_db_manager_instance.reset_mock()
    mock_db_manager_instance.get_all_people.side_effect = Exception("Connection failed")

    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_status"] == "unhealthy: Connection failed"
    mock_db_manager_instance.get_all_people.assert_called_once()
