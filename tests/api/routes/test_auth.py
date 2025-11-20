"""
Unit tests for the authentication API endpoints.
"""

import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from aws.backend.api.routes import auth

# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(auth.router)

client = TestClient(app)


class TestAuthEndpoints(unittest.TestCase):
    """Test suite for the authentication endpoints."""

    def test_login_success(self):
        """Test successful login with correct placeholder credentials."""
        # Arrange
        credentials = {"username": "admin", "password": "admin"}

        # Act
        response = client.post("/login", json=credentials)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["token_type"], "bearer")
        self.assertIn("access_token", data)

    def test_login_failure(self):
        """Test failed login with incorrect credentials."""
        # Arrange
        credentials = {"username": "user", "password": "wrong"}

        # Act
        response = client.post("/login", json=credentials)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid credentials")

    def test_refresh_token_not_implemented(self):
        """Test that the /refresh endpoint is not implemented."""
        # Act
        response = client.post("/refresh")

        # Assert
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()["detail"], "Token refresh not implemented")

    def test_logout_success(self):
        """Test the placeholder /logout endpoint."""
        # Act
        response = client.post("/logout")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Logged out successfully"})


if __name__ == "__main__":
    unittest.main()

