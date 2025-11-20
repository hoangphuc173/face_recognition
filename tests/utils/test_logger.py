"""
Unit tests for the centralized logging configuration.
"""

import json
import logging
import sys
import unittest
from unittest.mock import MagicMock, patch

from aws.backend.utils.logger import JSONFormatter, get_logger, setup_logger


class TestJSONFormatter(unittest.TestCase):
    """Test suite for the JSONFormatter class."""

    def test_format_basic_record(self):
        """Test formatting a basic log record into JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/app/test.py",
            lineno=10,
            msg="This is a test message",
            args=(),
            exc_info=None,
            func="test_func",
        )

        log_output = formatter.format(record)
        log_data = json.loads(log_output)

        self.assertEqual(log_data["level"], "INFO")
        self.assertEqual(log_data["logger"], "test_logger")
        self.assertEqual(log_data["message"], "This is a test message")
        self.assertIn("timestamp", log_data)

    def test_format_with_exception(self):
        """Test formatting a log record with exception info."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="error_logger",
                level=logging.ERROR,
                pathname="/app/error.py",
                lineno=20,
                msg="An error occurred",
                args=(),
                exc_info=sys.exc_info(),
                func="error_func",
            )

        log_output = formatter.format(record)
        log_data = json.loads(log_output)

        self.assertEqual(log_data["level"], "ERROR")
        self.assertIn("exception", log_data)
        self.assertIn("ValueError: Test exception", log_data["exception"])


class TestSetupLogger(unittest.TestCase):
    """Test suite for the setup_logger and get_logger functions."""

    @patch("logging.getLogger")
    def test_setup_logger_basic(self, mock_get_logger):
        """Test basic logger setup with a console handler."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = setup_logger("my_app", level="DEBUG")

        mock_get_logger.assert_called_with("my_app")
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_logger.handlers.clear.assert_called_once()
        self.assertEqual(mock_logger.addHandler.call_count, 1)

        handler = mock_logger.addHandler.call_args[0][0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertNotIsInstance(handler.formatter, JSONFormatter)

    @patch("logging.getLogger")
    def test_setup_logger_json_format(self, mock_get_logger):
        """Test logger setup with JSON formatting."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        setup_logger("my_app_json", json_format=True)

        handler = mock_logger.addHandler.call_args[0][0]
        self.assertIsInstance(handler.formatter, JSONFormatter)

    @patch("aws.backend.utils.logger.Path")
    @patch("logging.FileHandler")
    @patch("logging.getLogger")
    def test_setup_logger_with_file(self, mock_get_logger, mock_file_handler, mock_path_cls):
        """Test logger setup with both console and file handlers."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        log_file = "/var/log/app.log"

        setup_logger("my_app_file", log_file=log_file)

        mock_path_cls.assert_called_with(log_file)
        mock_path_cls.return_value.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_file_handler.assert_called_with(log_file)
        self.assertEqual(mock_logger.addHandler.call_count, 2)

    def test_get_logger_wrapper(self):
        """Test the get_logger convenience wrapper."""
        logger = get_logger("wrapper_test")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "wrapper_test")


if __name__ == "__main__":
    unittest.main()

