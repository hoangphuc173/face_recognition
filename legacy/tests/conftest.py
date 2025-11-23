# tests/conftest.py

import sys
import os

# Add the project root to the Python path so that modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Import the app and settings
# Important: Import after sys.path is modified
from aws.backend.api.app import app
from aws.backend.utils.config import settings

# ==================================================================
# Override settings for the entire test session
# ==================================================================

# Use a test-specific environment
settings.app_env = "test"
# Disable features that are not relevant for most tests
settings.enable_xray = False
settings.enable_cors = False
# Use a predictable, non-production auth mode
settings.auth_mode = "anonymous"


# ==================================================================
# Mocked AWS and Service Fixtures
# ==================================================================


@pytest.fixture(scope="function")
def mock_s3_client():
    """Fixture for a mocked S3Client."""
    mock = MagicMock()
    # Add default return values for common method calls if needed
    mock.upload_file_in_memory.return_value = "s3://test-bucket/test-key.jpg"
    return mock


@pytest.fixture(scope="function")
def mock_rekognition_client():
    """Fixture for a mocked RekognitionClient."""
    return MagicMock()


@pytest.fixture(scope="function")
def mock_dynamodb_client():
    """Fixture for a mocked DynamoDBClient."""
    mock = MagicMock()
    mock.check_health.return_value = {"status": "ok"}
    return mock


@pytest.fixture(scope="function")
def mock_enrollment_service():
    """Fixture for a mocked EnrollmentService."""
    return MagicMock()


@pytest.fixture(scope="function")
def mock_identification_service():
    """Fixture for a mocked IdentificationService."""
    return MagicMock()


@pytest.fixture(scope="function")
def mock_db_manager():
    """Fixture for a mocked DatabaseManager."""
    return MagicMock()


# ==================================================================
# Main Test Client Fixture
# ==================================================================


@pytest.fixture(scope="function")
def client(
    monkeypatch,
    mock_s3_client,
    mock_rekognition_client,
    mock_dynamodb_client,
    mock_enrollment_service,
    mock_identification_service,
    mock_db_manager,
):
    """
    Main fixture to get a TestClient with all services and clients mocked.

    This fixture patches the service instances at the module level of the `app`
    before creating the TestClient. This ensures all API calls use mocks.
    """
    # Patch the global service and client instances in the app module
    monkeypatch.setattr("aws.backend.api.app.s3_client", mock_s3_client)
    monkeypatch.setattr("aws.backend.api.app.rekognition_client", mock_rekognition_client)
    monkeypatch.setattr("aws.backend.api.app.dynamodb_client", mock_dynamodb_client)
    monkeypatch.setattr("aws.backend.api.app.enrollment_service", mock_enrollment_service)
    monkeypatch.setattr(
        "aws.backend.api.app.identification_service", mock_identification_service
    )
    monkeypatch.setattr("aws.backend.api.app.db_manager", mock_db_manager)

    # Yield the test client
    with TestClient(app) as test_client:
        yield test_client
