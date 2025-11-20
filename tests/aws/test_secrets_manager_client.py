"""
Unit tests for the Secrets Manager client.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from aws.backend.aws.secrets_manager_client import get_secret


class TestSecretsManagerClient(unittest.TestCase):
    """Test suite for the Secrets Manager client function."""

    def tearDown(self):
        """Clear the cache after each test to ensure isolation."""
        get_secret.cache_clear()

    @patch("aws.backend.aws.secrets_manager_client.boto3")
    def test_get_secret_success(self, mock_boto3):
        """Test successfully retrieving and parsing a secret."""
        # Arrange
        mock_sm_client = MagicMock()
        mock_boto3.session.Session.return_value.client.return_value = mock_sm_client

        secret_name = "my/secret"
        region_name = "us-east-1"
        secret_content = {"username": "admin", "password": "password123"}
        mock_sm_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_content)
        }

        # Act
        result = get_secret(secret_name, region_name)

        # Assert
        self.assertEqual(result, secret_content)
        mock_sm_client.get_secret_value.assert_called_once_with(SecretId=secret_name)

    @patch("aws.backend.aws.secrets_manager_client.boto3")
    def test_get_secret_cached(self, mock_boto3):
        """Test that the secret retrieval is cached."""
        # Arrange
        mock_sm_client = MagicMock()
        mock_boto3.session.Session.return_value.client.return_value = mock_sm_client

        secret_name = "my/cached/secret"
        region_name = "us-east-1"
        secret_content = {"api_key": "xyz-abc"}
        mock_sm_client.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_content)
        }

        # Act
        result1 = get_secret(secret_name, region_name)
        result2 = get_secret(secret_name, region_name)  # Call again

        # Assert
        self.assertEqual(result1, secret_content)
        self.assertEqual(result2, secret_content)
        # The mock should only be called once due to caching
        mock_sm_client.get_secret_value.assert_called_once_with(SecretId=secret_name)

    @patch("aws.backend.aws.secrets_manager_client.boto3")
    def test_get_secret_client_error(self, mock_boto3):
        """Test handling of ClientError from AWS."""
        # Arrange
        mock_sm_client = MagicMock()
        mock_boto3.session.Session.return_value.client.return_value = mock_sm_client

        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        side_effect = ClientError(error_response, "GetSecretValue")
        mock_sm_client.get_secret_value.side_effect = side_effect

        # Act
        result = get_secret("nonexistent/secret", "us-east-1")

        # Assert
        self.assertIsNone(result)

    @patch("aws.backend.aws.secrets_manager_client.boto3")
    def test_get_secret_no_secret_string(self, mock_boto3):
        """Test handling of a secret that has no SecretString."""
        # Arrange
        mock_sm_client = MagicMock()
        mock_boto3.session.Session.return_value.client.return_value = mock_sm_client
        mock_sm_client.get_secret_value.return_value = {"SecretBinary": b"data"}

        # Act
        result = get_secret("binary/secret", "us-east-1")

        # Assert
        self.assertIsNone(result)

    @patch("aws.backend.aws.secrets_manager_client.boto3")
    def test_get_secret_json_decode_error(self, mock_boto3):
        """Test handling of a secret with invalid JSON."""
        # Arrange
        mock_sm_client = MagicMock()
        mock_boto3.session.Session.return_value.client.return_value = mock_sm_client
        mock_sm_client.get_secret_value.return_value = {"SecretString": "not-valid-json"}

        # Act
        result = get_secret("bad/json/secret", "us-east-1")

        # Assert
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

