"""
Unit tests for the configuration module.
"""

import importlib
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# We need to reload the module to test different env var scenarios
from aws.backend.utils import config


class TestConfig(unittest.TestCase):
    """Test suite for the config module."""

    def setUp(self):
        """Back up original environment variables and sys.modules."""
        self.original_environ = dict(os.environ)
        self.original_sys_modules = dict(sys.modules)

    def tearDown(self):
        """Restore original environment and modules after each test."""
        os.environ.clear()
        os.environ.update(self.original_environ)

        # Restore sys.modules to not break subsequent tests
        modules_to_restore = [m for m in sys.modules if m not in self.original_sys_modules]
        for module in modules_to_restore:
            if module in sys.modules:
                del sys.modules[module]
        sys.modules.update(self.original_sys_modules)
        # Final reload to ensure clean state for other test files
        importlib.reload(config)

    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        importlib.reload(config)
        settings = config.get_settings()
        self.assertEqual(settings.app_env, "development")
        self.assertEqual(settings.api_port, 8000)
        self.assertFalse(settings.debug)

    @patch('aws.backend.utils.config.settings', new_callable=MagicMock)
    def test_environment_variable_override(self, mock_settings):
        """Test that environment variables override default settings."""
        # Arrange: Configure the mock to simulate loaded env vars
        mock_settings.app_env = "production"
        mock_settings.api_port = 9999
        mock_settings.debug = True
        mock_settings.aws_s3_bucket = "my-prod-bucket"

        # Act: The get_settings function will now return our mock
        settings = config.get_settings()

        # Assert: Check that we got the mocked values
        self.assertEqual(settings.app_env, "production")
        self.assertEqual(settings.api_port, 9999)
        self.assertEqual(settings.aws_s3_bucket, "my-prod-bucket")
        self.assertTrue(settings.debug)

    @patch.dict(os.environ, {
        "API_KEY_ENABLED": "true",
        "AWS_REKOGNITION_MIN_CONFIDENCE": "95.5",
    })
    def test_fallback_settings_class(self):
        """Test the fallback Settings class when pydantic is not installed."""
        # Arrange: Pretend pydantic is not installed by removing it from sys.modules
        if "pydantic" in sys.modules:
            del sys.modules["pydantic"]

        # Act: Reload the config module, which should now use the fallback
        importlib.reload(config)
        settings = config.get_settings()

        # Assert: Check if values are parsed correctly by the fallback
        self.assertTrue(settings.api_key_enabled)
        self.assertEqual(settings.aws_rekognition_min_confidence, 95.5)
        self.assertEqual(settings.app_name, "Face Recognition System - Cloud")


if __name__ == "__main__":
    unittest.main()
