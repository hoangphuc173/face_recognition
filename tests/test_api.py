# tests/test_api.py

import pytest
import base64
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock

from aws.backend.api.app import app, telemetry_events

# A valid base64 encoded 1x1 pixel red PNG
VALID_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAwAB/epv2AAAAABJRU5ErkJggg=="


@pytest.fixture
def mock_identification_service(monkeypatch):
    """Mock the identification_service used by the identify endpoint."""
    mock_service = MagicMock()
    # Simulate the return value of identification_service.identify_face
    mock_service.identify_face.return_value = {
        "success": True,
        "faces_detected": 1,
        "faces": [
            {
                "user_name": "test_user",
                "confidence": 0.99,
            }
        ],
    }
    monkeypatch.setattr("aws.backend.api.app.identification_service", mock_service)
    return mock_service


@pytest.mark.asyncio
async def test_telemetry_endpoint():
    """Test the /api/v1/telemetry endpoint."""
    telemetry_events.clear()
    test_payload = {
        "client_id": "test-client-123",
        "transport": "rest",
        "latency_ms": 150.5,
        "status": "success",
        "faces_detected": 1,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/telemetry", json=test_payload)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
    assert len(telemetry_events) == 1
    assert telemetry_events[0]["client_id"] == "test-client-123"


@pytest.mark.asyncio
async def test_identify_endpoint_success(mock_identification_service):
    """Test successful identification by sending multipart/form-data."""
    image_bytes = base64.b64decode(VALID_IMAGE_BASE64)
    files = {"image": ("test.png", image_bytes, "image/png")}
    data = {"threshold": "0.7"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/identify", files=files, data=data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert len(response_data["faces"]) == 1
    assert response_data["faces"][0]["user_name"] == "test_user"
    mock_identification_service.identify_face.assert_called_once()


@pytest.mark.asyncio
async def test_identify_endpoint_missing_image():
    """Test identify endpoint with missing image file in form-data."""
    data = {"threshold": "0.7"}  # Missing 'image' file

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/identify", data=data)

    # FastAPI returns 422 for validation errors like missing required form fields
    assert response.status_code == 422
