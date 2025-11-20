"""Unit tests for validators module."""

from aws.backend.utils.validators import DataValidator


def test_validate_user_name_success():
    is_valid, error = DataValidator.validate_user_name("Alice Nguyen")
    assert is_valid is True
    assert error is None


def test_validate_user_name_invalid():
    assert DataValidator.validate_user_name("")[0] is False
    assert DataValidator.validate_user_name("A")[0] is False
    long_name = "A" * 101
    assert DataValidator.validate_user_name(long_name)[0] is False


def test_validate_folder_name_rules():
    assert DataValidator.validate_folder_name("alice_01")[0] is True
    is_valid, error = DataValidator.validate_folder_name("Invalid-Name")
    assert is_valid is False
    assert "lowercase letters" in error


def test_validate_threshold_range():
    assert DataValidator.validate_threshold(0.5)[0] is True
    assert DataValidator.validate_threshold(-0.1)[0] is False
    assert DataValidator.validate_threshold(1.1)[0] is False


def test_validate_year_bounds():
    assert DataValidator.validate_year(None)[0] is True
    assert DataValidator.validate_year(1990)[0] is True
    assert DataValidator.validate_year(1800)[0] is False

