"""
Unit tests for the EnrollmentService class.
"""

import pytest
from unittest.mock import MagicMock, patch
from aws.backend.core.enrollment_service import EnrollmentService


@pytest.fixture
def enrollment_service(mock_s3_client, mock_rekognition_client, mock_dynamodb_client):
    """Fixture to create an EnrollmentService instance with mocked clients."""
    return EnrollmentService(
        s3_client=mock_s3_client,
        rekognition_client=mock_rekognition_client,
        dynamodb_client=mock_dynamodb_client,
    )


def test_init_requires_all_clients():
    """Test that EnrollmentService raises ValueError if any client is missing."""
    with pytest.raises(ValueError, match="All AWS clients"):
        EnrollmentService(
            s3_client=None,
            rekognition_client=MagicMock(),
            dynamodb_client=MagicMock(),
        )


def test_enroll_face_success(enrollment_service, mock_s3_client, mock_rekognition_client, mock_dynamodb_client):
    """Test successful face enrollment without duplicates."""
    # Arrange: Configure mocks for a successful enrollment
    mock_rekognition_client.search_faces.return_value = {
        "success": True,
        "matches": [],  # No duplicates
    }
    mock_s3_client.upload_bytes.return_value = {
        "success": True,
        "url": "s3://bucket/test.jpg",
    }
    mock_dynamodb_client.save_person.return_value = {"success": True}
    mock_dynamodb_client.get_person.return_value = {
        "success": True,
        "person": {"person_id": "person_123", "embedding_count": 0},
    }
    mock_dynamodb_client.update_person.return_value = {"success": True}
    mock_rekognition_client.index_face.return_value = {
        "success": True,
        "face_id": "face_abc123",
        "quality_score": 95.5,
    }
    mock_dynamodb_client.save_embedding.return_value = {"success": True}

    # Act: Call enroll_face
    result = enrollment_service.enroll_face(
        image_bytes=b"fake_image_data",
        user_name="Test User",
    )

    # Assert: Verify the result and that all clients were called correctly
    assert result["success"] is True
    assert result["user_name"] == "Test User"
    assert result["face_id"] == "face_abc123"
    assert result["duplicate_found"] is False
    
    # Verify client interactions
    mock_rekognition_client.search_faces.assert_called_once()
    mock_s3_client.upload_bytes.assert_called_once()
    mock_dynamodb_client.save_person.assert_called_once()
    mock_rekognition_client.index_face.assert_called_once()


def test_enroll_face_duplicate_detected(enrollment_service, mock_rekognition_client):
    """Test that enrollment stops when a duplicate face is detected."""
    # Arrange: Mock finding a duplicate
    mock_rekognition_client.search_faces.return_value = {
        "success": True,
        "matches": [
            {
                "external_image_id": "person_existing",
                "face_id": "face_existing",
                "similarity": 98.5,
            }
        ],
    }
    # Mock getting the existing person's info
    enrollment_service.db.get_person = MagicMock(return_value={
        "person_id": "person_existing",
        "user_name": "Existing User",
    })

    # Act: Call enroll_face
    result = enrollment_service.enroll_face(
        image_bytes=b"fake_image_data",
        user_name="Test User",
        check_duplicate=True,
    )

    # Assert: Verify duplicate was detected and enrollment was stopped
    assert result["success"] is False
    assert result["duplicate_found"] is True
    assert len(result["duplicate_info"]) == 1
    assert result["duplicate_info"][0]["user_name"] == "Existing User"
    
    # Verify that S3 upload was NOT called (enrollment stopped early)
    enrollment_service.s3.upload_bytes.assert_not_called()


def test_enroll_face_s3_upload_fails(enrollment_service, mock_s3_client, mock_rekognition_client):
    """Test enrollment failure when S3 upload fails."""
    # Arrange: Mock no duplicates but S3 upload fails
    mock_rekognition_client.search_faces.return_value = {
        "success": True,
        "matches": [],
    }
    mock_s3_client.upload_bytes.return_value = {
        "success": False,
        "error": "S3 connection error",
    }

    # Act
    result = enrollment_service.enroll_face(
        image_bytes=b"fake_image_data",
        user_name="Test User",
    )

    # Assert
    assert result["success"] is False
    assert "Failed to upload image" in result["message"]
    
    # Verify Rekognition indexing was NOT called
    mock_rekognition_client.index_face.assert_not_called()


def test_enroll_face_rekognition_fails_with_rollback(
    enrollment_service, 
    mock_s3_client, 
    mock_rekognition_client, 
    mock_dynamodb_client
):
    """Test that person is deleted (rollback) when Rekognition indexing fails."""
    # Arrange: Mock successful steps up to Rekognition, then fail
    mock_rekognition_client.search_faces.return_value = {
        "success": True,
        "matches": [],
    }
    mock_s3_client.upload_bytes.return_value = {
        "success": True,
        "url": "s3://bucket/test.jpg",
    }
    mock_dynamodb_client.save_person.return_value = {"success": True}
    mock_rekognition_client.index_face.return_value = {
        "success": False,
        "error": "No face detected",
    }
    mock_dynamodb_client.delete_person.return_value = {"success": True}

    # Act
    result = enrollment_service.enroll_face(
        image_bytes=b"fake_image_data",
        user_name="Test User",
    )

    # Assert
    assert result["success"] is False
    assert "Failed to index face" in result["message"]
    
    # Verify rollback: delete_person should have been called
    mock_dynamodb_client.delete_person.assert_called_once()

