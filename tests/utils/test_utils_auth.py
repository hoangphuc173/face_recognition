"""
Unit tests for authentication helpers.
"""

import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from jwt import InvalidTokenError

from aws.backend.utils import auth


class TestAuthHelpers(unittest.TestCase):
    """Test suite for authentication helper functions."""

    def test_extract_bearer_token(self):
        """Test the _extract_bearer_token function."""
        self.assertEqual(auth._extract_bearer_token("Bearer my-token"), "my-token")
        self.assertEqual(auth._extract_bearer_token("bearer my-token"), "my-token")
        self.assertIsNone(auth._extract_bearer_token("Bearer"))
        self.assertIsNone(auth._extract_bearer_token("Token my-token"))
        self.assertIsNone(auth._extract_bearer_token(None))

    def test_require_admin_success(self):
        """Test that require_admin passes for admin users."""
        try:
            auth.require_admin({"groups": ["admin", "user"]})
        except HTTPException:
            self.fail("require_admin() raised HTTPException unexpectedly!")

    def test_require_admin_failure(self):
        """Test that require_admin fails for non-admin users."""
        with self.assertRaises(HTTPException) as cm:
            auth.require_admin({"groups": ["user"]})
        self.assertEqual(cm.exception.status_code, 403)

        with self.assertRaises(HTTPException) as cm:
            auth.require_admin({})
        self.assertEqual(cm.exception.status_code, 403)


    @patch("aws.backend.utils.auth.jwt_decode")
    @patch("aws.backend.utils.auth._jwk_client")
    def test_verify_cognito_token_success(self, mock_jwk_client, mock_jwt_decode):
        """Test successful Cognito token verification."""
        # Arrange
        mock_key = MagicMock()
        mock_jwk_client.return_value.get_signing_key_from_jwt.return_value = mock_key
        mock_jwt_decode.return_value = {"cognito:groups": ["user"]}

        # Act
        claims = auth._verify_cognito_token("valid-token")

        # Assert
        self.assertIn("user", claims["groups"])
        mock_jwt_decode.assert_called_once()

    @patch("aws.backend.utils.auth._jwk_client")
    def test_verify_cognito_token_disabled(self, mock_jwk_client):
        """Test token verification when Cognito is disabled."""
        # Arrange
        mock_jwk_client.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as cm:
            auth._verify_cognito_token("any-token")
        self.assertEqual(cm.exception.status_code, 401)
        self.assertEqual(cm.exception.detail, "Cognito disabled")

    @patch("aws.backend.utils.auth.jwt_decode")
    @patch("aws.backend.utils.auth._jwk_client")
    def test_verify_cognito_token_invalid(self, mock_jwk_client, mock_jwt_decode):
        """Test token verification with an invalid token."""
        # Arrange
        mock_key = MagicMock()
        mock_jwk_client.return_value.get_signing_key_from_jwt.return_value = mock_key
        mock_jwt_decode.side_effect = InvalidTokenError("Token is expired")

        # Act & Assert
        with self.assertRaises(HTTPException) as cm:
            auth._verify_cognito_token("invalid-token")
        self.assertEqual(cm.exception.status_code, 401)
        self.assertEqual(cm.exception.detail, "Invalid token")


    @patch("aws.backend.utils.auth._verify_cognito_token")
    def test_authenticate_request_with_cognito_token(self, mock_verify):
        """Test successful authentication with a Cognito token."""
        # Arrange
        mock_verify.return_value = {"groups": ["user"]}
        headers = {"authorization": "Bearer valid-token"}

        # Act
        claims = auth.authenticate_request(headers=headers)

        # Assert
        self.assertEqual(claims, {"groups": ["user"]})
        mock_verify.assert_called_once_with("valid-token")


    @patch("aws.backend.utils.auth.settings")
    @patch("aws.backend.utils.auth._verify_cognito_token")
    def test_authenticate_request_with_api_key(self, mock_verify, mock_settings):
        """Test successful authentication with a valid API key."""
        # Arrange
        mock_settings.api_key_enabled = True
        mock_settings.api_key_header = "X-API-Key"
        mock_settings.api_key_value = "secret-key"
        mock_settings.cognito_enabled = False  # Isolate API key logic

        headers = {"x-api-key": "secret-key"}

        # Act
        claims = auth.authenticate_request(headers=headers)

        # Assert
        self.assertEqual(claims, {"auth": "api_key", "groups": ["admin"]})
        mock_verify.assert_not_called()


    @patch("aws.backend.utils.auth.settings")
    def test_authenticate_request_invalid_api_key(self, mock_settings):
        """Test authentication failure with an invalid API key."""
        # Arrange
        mock_settings.api_key_enabled = True
        mock_settings.api_key_header = "X-API-Key"
        mock_settings.api_key_value = "secret-key"
        mock_settings.cognito_enabled = False

        headers = {"x-api-key": "wrong-key"}

        # Act & Assert
        with self.assertRaises(HTTPException) as cm:
            auth.authenticate_request(headers=headers)
        self.assertEqual(cm.exception.status_code, 401)
        self.assertEqual(cm.exception.detail, "Invalid API key")

    @patch("aws.backend.utils.auth.settings")
    def test_authenticate_request_no_auth_cognito_enabled(self, mock_settings):
        """Test auth failure when no token is provided and Cognito is enabled."""
        # Arrange
        mock_settings.api_key_enabled = False
        mock_settings.cognito_enabled = True

        # Act & Assert
        with self.assertRaises(HTTPException) as cm:
            auth.authenticate_request(headers={})
        self.assertEqual(cm.exception.status_code, 401)
        self.assertEqual(cm.exception.detail, "Authorization token required")

    @patch("aws.backend.utils.auth.settings")
    def test_authenticate_request_no_auth_enabled(self, mock_settings):
        """Test anonymous access when no authentication methods are enabled."""
        # Arrange
        mock_settings.api_key_enabled = False
        mock_settings.cognito_enabled = False

        # Act
        claims = auth.authenticate_request(headers={})

        # Assert
        self.assertEqual(claims, {"auth": "anonymous", "groups": []})


    @patch("aws.backend.utils.auth.requests")
    @patch("aws.backend.utils.auth.settings")
    @patch("aws.backend.utils.auth._issuer")
    def test_fetch_cognito_jwks_success(self, mock_issuer, mock_settings, mock_requests):
        """Test successfully fetching Cognito JWKS."""
        # Arrange
        mock_settings.cognito_enabled = True
        mock_issuer.return_value = "http://fake-issuer"
        mock_response = MagicMock()
        mock_response.json.return_value = {"keys": ["key1"]}
        mock_requests.get.return_value = mock_response

        # Act
        result = auth.fetch_cognito_jwks()

        # Assert
        self.assertEqual(result, {"keys": ["key1"]})
        mock_requests.get.assert_called_once_with("http://fake-issuer/.well-known/jwks.json", timeout=5)
        mock_response.raise_for_status.assert_called_once()

    @patch("aws.backend.utils.auth.settings")
    def test_fetch_cognito_jwks_disabled(self, mock_settings):
        """Test fetching JWKS when Cognito is disabled."""
        # Arrange
        mock_settings.cognito_enabled = False

        # Act
        result = auth.fetch_cognito_jwks()

        # Assert
        self.assertEqual(result, {})

    @patch("aws.backend.utils.auth.requests")
    @patch("aws.backend.utils.auth.settings")
    def test_fetch_cognito_jwks_request_error(self, mock_settings, mock_requests):
        """Test fetching JWKS when the HTTP request fails."""
        # Arrange
        mock_settings.cognito_enabled = True
        mock_requests.get.side_effect = Exception("Request failed")

        # Act & Assert
        with self.assertRaises(Exception):
            auth.fetch_cognito_jwks()


if __name__ == "__main__":
    unittest.main()

