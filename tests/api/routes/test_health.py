"""
Unit tests for the health check API endpoints.
"""

import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

# The router to be tested
from aws.backend.api.routes import health
from aws.backend.utils.config import get_settings

# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(health.router)


class TestHealthEndpoints(unittest.TestCase):
    """Test suite for the health, readiness, and liveness endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    @patch("aws.backend.api.routes.health.DatabaseManager")
    def test_health_check_success(self, mock_db_manager):
        """Test the /health endpoint with a healthy database connection."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.app_env = "test"
        mock_settings.db_path = "/tmp/fake.db"

        def override_get_settings():
            return mock_settings

        app.dependency_overrides[get_settings] = override_get_settings

        # Act
        response = self.client.get("/health")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database_status"], "healthy")
        self.assertEqual(data["environment"], "test")
        mock_db_manager.assert_called_with("/tmp/fake.db")

        # Clean up
        app.dependency_overrides.clear()

    @patch("aws.backend.api.routes.health.DatabaseManager")
    def test_health_check_db_error(self, mock_db_manager):
        """Test the /health endpoint with an unhealthy database connection."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.app_env = "test"
        mock_settings.db_path = "/tmp/fake.db"
        mock_db_manager.return_value.get_all_people.side_effect = Exception("DB connection failed")

        def override_get_settings():
            return mock_settings

        app.dependency_overrides[get_settings] = override_get_settings

        # Act
        response = self.client.get("/health")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database_status"], "unhealthy: DB connection failed")

        # Clean up
        app.dependency_overrides.clear()

    @patch("aws.backend.api.routes.health.DatabaseManager")
    def test_readiness_check_success(self, mock_db_manager):
        """Test the /ready endpoint when the database is accessible."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.db_path = "/tmp/fake.db"
        mock_db_manager.return_value.get_all_people.return_value = []

        def override_get_settings():
            return mock_settings

        app.dependency_overrides[get_settings] = override_get_settings

        # Act
        response = self.client.get("/ready")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})

        # Clean up
        app.dependency_overrides.clear()

    @patch("aws.backend.api.routes.health.DatabaseManager")
    def test_readiness_check_failure(self, mock_db_manager):
        """Test the /ready endpoint when the database is not accessible."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.db_path = "/tmp/fake.db"
        mock_db_manager.return_value.get_all_people.side_effect = Exception("DB Error")

        def override_get_settings():
            return mock_settings

        app.dependency_overrides[get_settings] = override_get_settings

        # Act
        response = self.client.get("/ready")

        # Assert
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "not ready", "error": "DB Error"})

        # Clean up
        app.dependency_overrides.clear()

    def test_liveness_check(self):
        """Test the /live endpoint."""
        # Act
        response = self.client.get("/live")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "alive"})


if __name__ == "__main__":
    unittest.main()
