"""
Unit tests for the identification API endpoint.
"""

import unittest
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from aws.backend.api.routes import identify

# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(identify.router)


class TestIdentifyEndpoint(unittest.TestCase):
    """Test suite for the /identify endpoint."""

    def setUp(self):
        self.client = TestClient(app)
        self.mock_identification_service = MagicMock()

        # Override the dependency with the mock
        app.dependency_overrides[identify.get_identification_service] = lambda: self.mock_identification_service

    def tearDown(self):
        # Clear the dependency overrides after each test
        app.dependency_overrides.clear()

    def test_identify_face_success(self):
        """Test successful face identification."""
        # Arrange
        self.mock_identification_service.identify_face.return_value = {
            "success": True,
            "faces": [
                {
                    "person_id": "person-123",
                    "user_name": "John Doe",
                    "gender": "Male",
                    "birth_year": "1990",
                    "hometown": "Anytown",
                    "residence": "Anycity",
                    "confidence": 0.99,
                    "similarity": 99.0,
                    "face_id": "face-abc",
                    "match_time": "2023-01-01T12:00:00Z",
                }
            ],
        }

        # Act
        with open("fake_image.jpg", "wb") as f:
            f.write(b"fake image data")
        
        with open("fake_image.jpg", "rb") as f:
            response = self.client.post(
                "/identify",
                files={"image": ("test.jpg", f, "image/jpeg")},
            )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["faces"]), 1)
        self.assertEqual(data["faces"][0]["person_id"], "person-123")
        self.mock_identification_service.identify_face.assert_called_once()

    def test_identify_face_failure(self):
        """Test failed face identification when the service returns an error."""
        # Arrange
        self.mock_identification_service.identify_face.return_value = {
            "success": False,
            "message": "No faces found in the image.",
        }

        # Act
        with open("fake_image.jpg", "wb") as f:
            f.write(b"fake image data")

        with open("fake_image.jpg", "rb") as f:
            response = self.client.post(
                "/identify",
                files={"image": ("test.jpg", f, "image/jpeg")},
            )

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "No faces found in the image.")

    def test_identify_face_unexpected_error(self):
        """Test an unexpected server error during identification."""
        # Arrange
        self.mock_identification_service.identify_face.side_effect = Exception("AWS is down")

        # Act
        with open("fake_image.jpg", "wb") as f:
            f.write(b"fake image data")

        with open("fake_image.jpg", "rb") as f:
            response = self.client.post(
                "/identify",
                files={"image": ("test.jpg", f, "image/jpeg")},
            )

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIn("An unexpected error occurred", response.json()["detail"])


if __name__ == "__main__":
    import os
    # Clean up fake file if it exists
    if os.path.exists("fake_image.jpg"):
        os.remove("fake_image.jpg")
    unittest.main()
