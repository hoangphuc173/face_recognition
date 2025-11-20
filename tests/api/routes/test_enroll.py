"""
Unit tests for the enrollment API endpoint.
"""

import unittest
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from aws.backend.api.routes import enroll

# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(enroll.router)


class TestEnrollEndpoint(unittest.TestCase):
    """Test suite for the /enroll endpoint."""

    def setUp(self):
        self.client = TestClient(app)
        self.mock_enrollment_service = MagicMock()

        # Override the dependency with the mock
        app.dependency_overrides[enroll.get_enrollment_service] = lambda: self.mock_enrollment_service

    def tearDown(self):
        # Clear the dependency overrides after each test
        app.dependency_overrides.clear()

    def test_enroll_face_success(self):
        """Test successful face enrollment."""
        # Arrange
        self.mock_enrollment_service.enroll_face.return_value = {
            "success": True,
            "person_id": "person-123",
            "face_id": "face-abc",
            "message": "Enrollment successful.",
        }

        # Act
        with open("fake_image.jpg", "wb") as f:
            f.write(b"fake image data")
        
        with open("fake_image.jpg", "rb") as f:
            response = self.client.post(
                "/enroll",
                files={"image": ("test.jpg", f, "image/jpeg")},
                data={"name": "John Doe"},
            )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["person_id"], "person-123")
        self.assertEqual(data["message"], "Enrollment successful.")
        self.mock_enrollment_service.enroll_face.assert_called_once()

    def test_enroll_face_failure(self):
        """Test failed face enrollment when the service returns an error."""
        # Arrange
        self.mock_enrollment_service.enroll_face.return_value = {
            "success": False,
            "message": "No face detected in the image.",
        }

        # Act
        with open("fake_image.jpg", "wb") as f:
            f.write(b"fake image data")

        with open("fake_image.jpg", "rb") as f:
            response = self.client.post(
                "/enroll",
                files={"image": ("test.jpg", f, "image/jpeg")},
                data={"name": "Jane Doe"},
            )

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "No face detected in the image.")

    def test_enroll_face_unexpected_error(self):
        """Test an unexpected server error during enrollment."""
        # Arrange
        self.mock_enrollment_service.enroll_face.side_effect = Exception("Something broke")

        # Act
        with open("fake_image.jpg", "wb") as f:
            f.write(b"fake image data")

        with open("fake_image.jpg", "rb") as f:
            response = self.client.post(
                "/enroll",
                files={"image": ("test.jpg", f, "image/jpeg")},
                data={"name": "Crash Test"},
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

