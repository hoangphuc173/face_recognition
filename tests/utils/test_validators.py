"""
Unit tests for data and file validators.
"""

import unittest
from unittest.mock import MagicMock, patch

from aws.backend.utils.validators import DataValidator, FileValidator


class TestDataValidator(unittest.TestCase):
    """Test suite for the DataValidator class."""

    def test_validate_user_name(self):
        """Test user name validation."""
        self.assertEqual(DataValidator.validate_user_name("John Doe"), (True, None))
        self.assertFalse(DataValidator.validate_user_name("")[0])
        self.assertFalse(DataValidator.validate_user_name("  ")[0])
        self.assertFalse(DataValidator.validate_user_name("A")[0])
        self.assertFalse(DataValidator.validate_user_name("A" * 101)[0])

    def test_validate_folder_name(self):
        """Test folder name validation."""
        self.assertEqual(DataValidator.validate_folder_name("my_folder_123"), (True, None))
        self.assertFalse(DataValidator.validate_folder_name("")[0])
        self.assertFalse(DataValidator.validate_folder_name("MyFolder")[0])  # Uppercase
        self.assertFalse(DataValidator.validate_folder_name("folder-name")[0])  # Hyphen
        self.assertFalse(DataValidator.validate_folder_name("folder name")[0])  # Space

    def test_validate_threshold(self):
        """Test recognition threshold validation."""
        self.assertEqual(DataValidator.validate_threshold(0.0), (True, None))
        self.assertEqual(DataValidator.validate_threshold(0.75), (True, None))
        self.assertEqual(DataValidator.validate_threshold(1.0), (True, None))
        self.assertFalse(DataValidator.validate_threshold(-0.1)[0])
        self.assertFalse(DataValidator.validate_threshold(1.1)[0])

    def test_validate_year(self):
        """Test birth year validation."""
        self.assertEqual(DataValidator.validate_year(1995), (True, None))
        self.assertEqual(DataValidator.validate_year(None), (True, None))
        self.assertFalse(DataValidator.validate_year(1899)[0])
        self.assertFalse(DataValidator.validate_year(2026)[0])



class TestFileValidator(unittest.TestCase):
    """Test suite for the FileValidator class."""

    @patch('aws.backend.utils.validators.Image')
    @patch('aws.backend.utils.validators.Path')
    def test_validate_image_success(self, mock_path_cls, mock_image_cls):
        """Test successful image validation."""
        # Arrange
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".jpg"
        mock_path_instance.stat.return_value.st_size = 1024  # 1KB
        mock_path_cls.return_value = mock_path_instance

        # Act
        is_valid, message = FileValidator.validate_image("fake/path.jpg")

        # Assert
        self.assertTrue(is_valid)
        self.assertIsNone(message)
        mock_image_cls.open.assert_called_once_with(mock_path_instance)

    @patch('aws.backend.utils.validators.Path')
    def test_validate_image_does_not_exist(self, mock_path_cls):
        """Test image validation when file does not exist."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path_cls.return_value = mock_path_instance

        is_valid, message = FileValidator.validate_image("nonexistent/path.jpg")

        self.assertFalse(is_valid)
        self.assertEqual(message, "File does not exist")

    @patch('aws.backend.utils.validators.Path')
    def test_validate_image_invalid_extension(self, mock_path_cls):
        """Test image validation with an invalid file extension."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".txt"
        mock_path_cls.return_value = mock_path_instance

        is_valid, message = FileValidator.validate_image("fake/path.txt")

        self.assertFalse(is_valid)
        self.assertIn("Invalid extension", message)

    @patch('aws.backend.utils.validators.Path')
    def test_validate_image_too_large(self, mock_path_cls):
        """Test image validation when file is too large."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".jpg"
        mock_path_instance.stat.return_value.st_size = FileValidator.MAX_FILE_SIZE + 1
        mock_path_cls.return_value = mock_path_instance

        is_valid, message = FileValidator.validate_image("fake/large_image.jpg")

        self.assertFalse(is_valid)
        self.assertIn("File too large", message)

    @patch('aws.backend.utils.validators.Image')
    @patch('aws.backend.utils.validators.Path')
    def test_validate_image_invalid_image_file(self, mock_path_cls, mock_image_cls):
        """Test image validation with a corrupted or invalid image file."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".jpg"
        mock_path_instance.stat.return_value.st_size = 1024
        mock_path_cls.return_value = mock_path_instance

        mock_image_cls.open.side_effect = Exception("Corrupted file")

        is_valid, message = FileValidator.validate_image("fake/corrupted.jpg")

        self.assertFalse(is_valid)
        self.assertIn("Invalid image file", message)


    @patch('aws.backend.utils.validators.Path')
    def test_validate_video_success(self, mock_path_cls):
        """Test successful video validation."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".mp4"
        mock_path_instance.stat.return_value.st_size = 5 * 1024 * 1024
        mock_path_cls.return_value = mock_path_instance

        is_valid, message = FileValidator.validate_video("fake/video.mp4")

        self.assertTrue(is_valid)
        self.assertIsNone(message)

    @patch('aws.backend.utils.validators.Path')
    def test_validate_video_invalid_extension(self, mock_path_cls):
        """Test video validation with an invalid file extension."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".mkv"
        mock_path_cls.return_value = mock_path_instance

        is_valid, message = FileValidator.validate_video("fake/video.mkv")

        self.assertFalse(is_valid)
        self.assertIn("Invalid extension", message)

    @patch('aws.backend.utils.validators.Path')
    def test_validate_video_too_large(self, mock_path_cls):
        """Test video validation when the file is too large."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.suffix = ".mp4"
        mock_path_instance.stat.return_value.st_size = FileValidator.MAX_FILE_SIZE + 1
        mock_path_cls.return_value = mock_path_instance

        is_valid, message = FileValidator.validate_video("fake/large_video.mp4")

        self.assertFalse(is_valid)
        self.assertIn("File too large", message)


if __name__ == "__main__":
    unittest.main()

