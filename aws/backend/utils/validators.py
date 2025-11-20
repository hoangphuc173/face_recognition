"""Validators for Face Recognition System."""

import re
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image


class FileValidator:
    """Validate uploaded files."""

    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    def validate_image(cls, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate image file.

        Args:
            file_path: Path to image file

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            return False, "File does not exist"

        # Check extension
        if path.suffix.lower() not in cls.ALLOWED_IMAGE_EXTENSIONS:
            return False, f"Invalid extension. Allowed: {cls.ALLOWED_IMAGE_EXTENSIONS}"

        # Check file size
        if path.stat().st_size > cls.MAX_FILE_SIZE:
            return (
                False,
                f"File too large. Max size: {cls.MAX_FILE_SIZE / 1024 / 1024}MB",
            )

        # Try to open image
        try:
            with Image.open(path) as img:
                img.verify()
            return True, None
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"

    @classmethod
    def validate_video(cls, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate video file.

        Args:
            file_path: Path to video file

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            return False, "File does not exist"

        # Check extension
        if path.suffix.lower() not in cls.ALLOWED_VIDEO_EXTENSIONS:
            return False, f"Invalid extension. Allowed: {cls.ALLOWED_VIDEO_EXTENSIONS}"

        # Check file size
        if path.stat().st_size > cls.MAX_FILE_SIZE:
            return (
                False,
                f"File too large. Max size: {cls.MAX_FILE_SIZE / 1024 / 1024}MB",
            )

        return True, None


class DataValidator:
    """Validate input data."""

    @staticmethod
    def validate_user_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate user name.

        Args:
            name: User name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Name cannot be empty"

        if len(name) < 2:
            return False, "Name must be at least 2 characters"

        if len(name) > 100:
            return False, "Name cannot exceed 100 characters"

        return True, None

    @staticmethod
    def validate_folder_name(folder_name: str) -> Tuple[bool, Optional[str]]:
        """Validate folder name.

        Args:
            folder_name: Folder name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not folder_name or not folder_name.strip():
            return False, "Folder name cannot be empty"

        # Check for invalid characters
        if not re.match(r"^[a-z0-9_]+$", folder_name):
            return (
                False,
                "Folder name must contain only lowercase letters, numbers, and underscores",
            )

        return True, None

    @staticmethod
    def validate_threshold(threshold: float) -> Tuple[bool, Optional[str]]:
        """Validate recognition threshold.

        Args:
            threshold: Threshold value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not 0.0 <= threshold <= 1.0:
            return False, "Threshold must be between 0.0 and 1.0"

        return True, None

    @staticmethod
    def validate_year(year: Optional[int]) -> Tuple[bool, Optional[str]]:
        """Validate birth year.

        Args:
            year: Year to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if year is None:
            return True, None

        current_year = 2025
        if not 1900 <= year <= current_year:
            return False, f"Year must be between 1900 and {current_year}"

        return True, None
