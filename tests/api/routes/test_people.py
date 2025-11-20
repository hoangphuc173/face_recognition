"""
Unit tests for the people management API endpoints.
"""

import unittest
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from aws.backend.api.routes import people

# Create a minimal FastAPI app for testing
app = FastAPI()
app.include_router(people.router)


class TestPeopleEndpoints(unittest.TestCase):
    """Test suite for the /people and /stats endpoints."""

    def setUp(self):
        self.client = TestClient(app)
        self.mock_db_manager = MagicMock()

        # Override the dependency with the mock
        app.dependency_overrides[people.get_db_manager] = lambda: self.mock_db_manager

    def tearDown(self):
        # Clear the dependency overrides after each test
        app.dependency_overrides.clear()

    def test_list_people_success(self):
        """Test successfully listing all people."""
        self.mock_db_manager.get_all_people.return_value = [
            {"person_id": "p-1", "user_name": "John", "created_at": "t1", "embedding_count": 1},
            {"person_id": "p-2", "user_name": "Jane", "created_at": "t2", "embedding_count": 2},
        ]
        response = self.client.get("/people")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["people"]), 2)

    def test_get_person_success(self):
        """Test successfully getting a single person."""
        self.mock_db_manager.get_person.return_value = {"person_id": "p-1", "user_name": "John", "created_at": "t1", "embedding_count": 1}
        response = self.client.get("/people/p-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user_name"], "John")

    def test_get_person_not_found(self):
        """Test getting a person who does not exist."""
        self.mock_db_manager.get_person.return_value = None
        response = self.client.get("/people/p-404")
        self.assertEqual(response.status_code, 404)

    def test_update_person_success(self):
        """Test successfully updating a person."""
        self.mock_db_manager.get_person.side_effect = [
            {"person_id": "p-1"},  # First call for existence check
            {"person_id": "p-1", "user_name": "John Updated", "created_at": "t1", "embedding_count": 1} # Second call to get updated data
        ]
        update_payload = {"user_name": "John Updated"}
        response = self.client.put("/people/p-1", json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user_name"], "John Updated")
        self.mock_db_manager.update_person.assert_called_with("p-1", update_payload)

    def test_update_person_not_found(self):
        """Test updating a person who does not exist."""
        self.mock_db_manager.get_person.return_value = None
        response = self.client.put("/people/p-404", json={"user_name": "Ghost"})
        self.assertEqual(response.status_code, 404)

    def test_delete_person_success(self):
        """Test successfully deleting a person."""
        self.mock_db_manager.get_person.return_value = {"person_id": "p-1"}
        response = self.client.delete("/people/p-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "message": "Person deleted: p-1"})
        self.mock_db_manager.delete_person.assert_called_with("p-1")

    def test_delete_person_not_found(self):
        """Test deleting a person who does not exist."""
        self.mock_db_manager.get_person.return_value = None
        response = self.client.delete("/people/p-404")
        self.assertEqual(response.status_code, 404)

    def test_get_database_stats_success(self):
        """Test successfully getting database statistics."""
        self.mock_db_manager.get_all_people.return_value = [
            {"embedding_count": 2}, {"embedding_count": 3}
        ]
        response = self.client.get("/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_people"], 2)
        self.assertEqual(data["total_embeddings"], 5)

    def test_get_database_stats_error(self):
        """Test an error when getting database statistics."""
        self.mock_db_manager.get_all_people.side_effect = Exception("DB Down")
        response = self.client.get("/stats")
        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
