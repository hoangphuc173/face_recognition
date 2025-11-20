"""
Unit tests for the DatabaseManager class.
"""

import pytest
from unittest.mock import MagicMock, ANY
from aws.backend.core.database_manager import DatabaseManager

# Fixtures like mock_dynamodb_client are automatically available from conftest.py

@pytest.fixture
def db_manager(mock_dynamodb_client):
    """Fixture to create a DatabaseManager instance with a mocked DynamoDB client."""
    return DatabaseManager(aws_dynamodb_client=mock_dynamodb_client)


def test_init_requires_dynamodb_client():
    """Test that DatabaseManager raises ValueError if no DynamoDB client is provided."""
    with pytest.raises(ValueError, match="AWS DynamoDB client is required"):
        DatabaseManager(aws_dynamodb_client=None)


def test_create_person_success(db_manager, mock_dynamodb_client):
    """Test successful creation of a person."""
    # Configure the mock to return a success response
    mock_dynamodb_client.save_person.return_value = {"success": True}

    result = db_manager.create_person(user_name="Test User")

    # Assert that the save_person method was called on the mock client
    mock_dynamodb_client.save_person.assert_called_once()
    # Assert the result from DatabaseManager is correct
    assert result["success"] is True
    assert "person_id" in result
    assert "Test User" in result["message"]


def test_create_person_failure(db_manager, mock_dynamodb_client):
    """Test failed creation of a person."""
    # Configure the mock to return a failure response
    mock_dynamodb_client.save_person.return_value = {
        "success": False,
        "error": "DynamoDB error",
    }

    result = db_manager.create_person(user_name="Test User")

    mock_dynamodb_client.save_person.assert_called_once()
    assert result["success"] is False
    assert "Failed to create profile" in result["message"]


def test_get_person_found(db_manager, mock_dynamodb_client):
    """Test retrieving a person that exists."""
    person_data = {"person_id": "person_123", "user_name": "Found User"}
    mock_dynamodb_client.get_person.return_value = {
        "success": True,
        "person": person_data,
    }

    result = db_manager.get_person("person_123")

    mock_dynamodb_client.get_person.assert_called_with("person_123")
    assert result == person_data


def test_get_person_not_found(db_manager, mock_dynamodb_client):
    """Test retrieving a person that does not exist."""
    mock_dynamodb_client.get_person.return_value = {"success": False}

    result = db_manager.get_person("person_404")

    mock_dynamodb_client.get_person.assert_called_with("person_404")
    assert result is None


def test_add_embedding_success(db_manager, mock_dynamodb_client):
    """Test successfully adding an embedding and updating the person's count."""
    # Mock the return values for the sequence of calls
    mock_dynamodb_client.save_embedding.return_value = {"success": True}

    result = db_manager.add_embedding(
        person_id="person_123",
        face_id="face_abc",
        image_url="s3://bucket/key.jpg",
    )

    assert result["success"] is True
    # Check that save_embedding was called correctly
    mock_dynamodb_client.save_embedding.assert_called_once_with(
        ANY, increment_count=True
    )


def test_check_health(db_manager, mock_dynamodb_client):
    """Test that check_health correctly calls the client's method."""
    mock_dynamodb_client.check_health.return_value = {"status": "ok"}

    result = db_manager.check_health()

    mock_dynamodb_client.check_health.assert_called_once()
    assert result == {"status": "ok"}


def test_search_people_success(db_manager, mock_dynamodb_client):
    """Test successful search for people."""
    search_results = [
        {"person_id": "person_1", "user_name": "John Doe"},
        {"person_id": "person_2", "user_name": "Johnny Smith"},
    ]
    mock_dynamodb_client.search_people.return_value = {
        "success": True,
        "people": search_results,
    }

    result = db_manager.search_people("John")

    mock_dynamodb_client.search_people.assert_called_with("John")
    assert result == search_results


def test_search_people_failure(db_manager, mock_dynamodb_client):
    """Test failed search for people."""
    mock_dynamodb_client.search_people.return_value = {
        "success": False,
        "error": "Some error",
    }

    result = db_manager.search_people("Unknown")

    mock_dynamodb_client.search_people.assert_called_with("Unknown")
    assert result == []


def test_get_all_people_success(db_manager, mock_dynamodb_client):
    """Test successfully retrieving all people."""
    people_list = [
        {"person_id": "person_1", "user_name": "Alice", "embedding_count": 3},
        {"person_id": "person_2", "user_name": "Bob", "embedding_count": 5},
    ]
    mock_dynamodb_client.list_people.return_value = {
        "success": True,
        "people": people_list,
    }

    result = db_manager.get_all_people()

    mock_dynamodb_client.list_people.assert_called_once()
    assert result == people_list
    assert len(result) == 2


def test_get_all_people_empty(db_manager, mock_dynamodb_client):
    """Test retrieving all people when database is empty."""
    mock_dynamodb_client.list_people.return_value = {
        "success": True,
        "people": [],
    }

    result = db_manager.get_all_people()

    mock_dynamodb_client.list_people.assert_called_once()
    assert result == []


def test_get_all_people_failure(db_manager, mock_dynamodb_client):
    """Test failed retrieval of all people."""
    mock_dynamodb_client.list_people.return_value = {
        "success": False,
        "error": "Database connection error",
    }

    result = db_manager.get_all_people()

    mock_dynamodb_client.list_people.assert_called_once()
    assert result == []


def test_delete_person_success(db_manager, mock_dynamodb_client):
    """Test successfully deleting a person."""
    mock_dynamodb_client.delete_person.return_value = {
        "success": True,
        "message": "Person deleted successfully",
    }

    result = db_manager.delete_person("person_123")

    mock_dynamodb_client.delete_person.assert_called_with("person_123")
    assert result["success"] is True


def test_delete_person_failure(db_manager, mock_dynamodb_client):
    """Test failed deletion of a person."""
    mock_dynamodb_client.delete_person.return_value = {
        "success": False,
        "error": "Person not found",
    }

    result = db_manager.delete_person("person_404")

    mock_dynamodb_client.delete_person.assert_called_with("person_404")
    assert result["success"] is False


def test_update_person_success(db_manager, mock_dynamodb_client):
    """Test successfully updating a person."""
    mock_dynamodb_client.update_person.return_value = {
        "success": True,
        "message": "Person updated successfully",
    }

    updates = {"user_name": "Updated Name", "gender": "Male"}
    result = db_manager.update_person("person_123", updates)

    mock_dynamodb_client.update_person.assert_called_once()
    call_args = mock_dynamodb_client.update_person.call_args
    assert call_args[0][0] == "person_123"
    assert call_args[0][1]["user_name"] == "Updated Name"
    assert call_args[0][1]["gender"] == "Male"
    assert "updated_at" in call_args[0][1]
    assert result["success"] is True


def test_update_person_failure(db_manager, mock_dynamodb_client):
    """Test failed update of a person."""
    mock_dynamodb_client.update_person.return_value = {
        "success": False,
        "error": "Person not found",
    }

    updates = {"user_name": "Ghost User"}
    result = db_manager.update_person("person_404", updates)

    mock_dynamodb_client.update_person.assert_called_once()
    assert result["success"] is False


def test_get_embeddings_success(db_manager, mock_dynamodb_client):
    """Test successfully retrieving embeddings for a person."""
    embeddings_list = [
        {"embedding_id": "emb_1", "person_id": "person_123", "face_id": "face_abc"},
        {"embedding_id": "emb_2", "person_id": "person_123", "face_id": "face_def"},
    ]
    mock_dynamodb_client.get_embeddings_by_person.return_value = {
        "success": True,
        "embeddings": embeddings_list,
    }

    result = db_manager.get_embeddings("person_123")

    mock_dynamodb_client.get_embeddings_by_person.assert_called_with("person_123")
    assert result == embeddings_list
    assert len(result) == 2


def test_get_embeddings_failure(db_manager, mock_dynamodb_client):
    """Test failed retrieval of embeddings."""
    mock_dynamodb_client.get_embeddings_by_person.return_value = {
        "success": False,
        "error": "Database error",
    }

    result = db_manager.get_embeddings("person_123")

    mock_dynamodb_client.get_embeddings_by_person.assert_called_with("person_123")
    assert result == []
