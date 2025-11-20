"""
Unit tests for the DynamoDBClient.
"""

import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from aws.backend.aws.dynamodb_client import DynamoDBClient


class TestDynamoDBClient(unittest.TestCase):
    """Test suite for DynamoDBClient."""

    @patch("aws.backend.aws.dynamodb_client.boto3")
    def setUp(self, mock_boto3):
        """Set up a mock DynamoDB client before each test."""
        self.mock_dynamodb_resource = MagicMock()
        self.mock_table = MagicMock()
        self.mock_dynamodb_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = self.mock_dynamodb_resource

        self.region = "us-east-1"
        self.people_table = "people"
        self.embeddings_table = "embeddings"
        self.matches_table = "matches"

        self.dynamodb_client = DynamoDBClient(
            region=self.region,
            people_table=self.people_table,
            embeddings_table=self.embeddings_table,
            matches_table=self.matches_table,
            enabled=True,
        )

    def test_init_success(self):
        """Test successful initialization."""
        self.assertTrue(self.dynamodb_client.enabled)
        self.assertIsNotNone(self.dynamodb_client.dynamodb)

    def test_init_disabled(self):
        """Test initialization when disabled."""
        client = DynamoDBClient(
            region=self.region,
            people_table=self.people_table,
            embeddings_table=self.embeddings_table,
            matches_table=self.matches_table,
            enabled=False,
        )
        self.assertFalse(client.enabled)
        self.assertIsNone(client.dynamodb)

    def test_save_person_success(self):
        """Test successfully saving a person."""
        # Arrange
        person_data = {"person_id": "p-123", "user_name": "John Doe", "age": 30.5}

        # Act
        result = self.dynamodb_client.save_person(person_data)

        # Assert
        self.assertTrue(result["success"])
        self.mock_dynamodb_resource.Table.assert_called_with(self.people_table)
        # Check that float is converted to Decimal
        args, kwargs = self.mock_table.put_item.call_args
        self.assertIsInstance(kwargs["Item"]["age"], Decimal)
        self.assertIn("created_at", kwargs["Item"])

    def test_save_person_api_error(self):
        """Test saving a person when DynamoDB API fails."""
        # Arrange
        self.mock_table.put_item.side_effect = Exception("DynamoDB Error")
        person_data = {"person_id": "p-123", "user_name": "John Doe"}

        # Act
        result = self.dynamodb_client.save_person(person_data)

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "DynamoDB Error")


    def test_get_person_success(self):
        """Test successfully getting a person."""
        # Arrange
        person_id = "p-123"
        expected_item = {"person_id": person_id, "user_name": "Jane Doe"}
        self.mock_table.get_item.return_value = {"Item": expected_item}

        # Act
        result = self.dynamodb_client.get_person(person_id)

        # Assert
        self.assertEqual(result, expected_item)
        self.mock_table.get_item.assert_called_once_with(Key={"person_id": person_id})

    def test_get_person_not_found(self):
        """Test getting a person who does not exist."""
        # Arrange
        self.mock_table.get_item.return_value = {}

        # Act
        result = self.dynamodb_client.get_person("p-404")

        # Assert
        self.assertIsNone(result)

    def test_get_person_api_error(self):
        """Test getting a person when the DynamoDB API fails."""
        # Arrange
        self.mock_table.get_item.side_effect = Exception("DynamoDB Error")

        # Act
        result = self.dynamodb_client.get_person("p-error")

        # Assert
        self.assertIsNone(result)


    def test_list_people_success(self):
        """Test successfully listing people."""
        # Arrange
        expected_items = [{"person_id": "p-1"}, {"person_id": "p-2"}]
        self.mock_table.scan.return_value = {"Items": expected_items}

        # Act
        result = self.dynamodb_client.list_people(limit=10)

        # Assert
        self.assertEqual(result, expected_items)
        self.mock_dynamodb_resource.Table.assert_called_with(self.people_table)
        self.mock_table.scan.assert_called_once_with(Limit=10)

    def test_list_people_api_error(self):
        """Test listing people when the DynamoDB API fails."""
        # Arrange
        self.mock_table.scan.side_effect = Exception("DynamoDB Error")

        # Act
        result = self.dynamodb_client.list_people()

        # Assert
        self.assertEqual(result, [])


    def test_search_people_success(self):
        """Test successfully searching for people."""
        # Arrange
        query = "John"
        expected_items = [{"person_id": "p-1", "user_name": "John Doe"}]
        self.mock_table.scan.return_value = {"Items": expected_items}

        # Act
        result = self.dynamodb_client.search_people(query, limit=10)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["people"], expected_items)
        self.mock_dynamodb_resource.Table.assert_called_with(self.people_table)
        # We expect scan to be called, but asserting the FilterExpression is complex.
        # So we just check that scan was called.
        self.mock_table.scan.assert_called_once()

    def test_search_people_api_error(self):
        """Test searching for people when the DynamoDB API fails."""
        # Arrange
        self.mock_table.scan.side_effect = Exception("DynamoDB Error")

        # Act
        result = self.dynamodb_client.search_people("query")

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["people"], [])
        self.assertEqual(result["error"], "DynamoDB Error")


    def test_save_embedding_success(self):
        """Test successfully saving an embedding."""
        # Arrange
        embedding_data = {
            "embedding_id": "e-123",
            "person_id": "p-123",
            "quality_score": 0.98,
        }

        # Act
        result = self.dynamodb_client.save_embedding(embedding_data)

        # Assert
        self.assertTrue(result["success"])
        self.mock_dynamodb_resource.Table.assert_called_with(self.embeddings_table)
        args, kwargs = self.mock_table.put_item.call_args
        self.assertIsInstance(kwargs["Item"]["quality_score"], Decimal)
        self.assertIn("created_at", kwargs["Item"])

    def test_save_embedding_api_error(self):
        """Test saving an embedding when the DynamoDB API fails."""
        # Arrange
        self.mock_table.put_item.side_effect = Exception("DynamoDB Error")
        embedding_data = {"embedding_id": "e-123", "person_id": "p-123"}

        # Act
        result = self.dynamodb_client.save_embedding(embedding_data)

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "DynamoDB Error")


    def test_get_embeddings_by_person_success(self):
        """Test successfully getting embeddings for a person."""
        # Arrange
        person_id = "p-123"
        expected_items = [{"embedding_id": "e-1"}, {"embedding_id": "e-2"}]
        self.mock_table.query.return_value = {"Items": expected_items}

        # Act
        result = self.dynamodb_client.get_embeddings_by_person(person_id)

        # Assert
        self.assertEqual(result, expected_items)
        self.mock_dynamodb_resource.Table.assert_called_with(self.embeddings_table)
        self.mock_table.query.assert_called_once_with(
            IndexName="person_id-index",
            KeyConditionExpression="person_id = :pid",
            ExpressionAttributeValues={":pid": person_id},
        )

    def test_get_embeddings_by_person_api_error(self):
        """Test getting embeddings when the DynamoDB API fails."""
        # Arrange
        self.mock_table.query.side_effect = Exception("DynamoDB Error")

        # Act
        result = self.dynamodb_client.get_embeddings_by_person("p-error")

        # Assert
        self.assertEqual(result, [])


    def test_save_match_success(self):
        """Test successfully saving a match."""
        # Arrange
        match_data = {"match_id": "m-123", "person_id": "p-123", "confidence": 99.5}

        # Act
        result = self.dynamodb_client.save_match(match_data)

        # Assert
        self.assertTrue(result["success"])
        self.mock_dynamodb_resource.Table.assert_called_with(self.matches_table)
        args, kwargs = self.mock_table.put_item.call_args
        self.assertIsInstance(kwargs["Item"]["confidence"], Decimal)
        self.assertIn("timestamp", kwargs["Item"])

    def test_save_match_api_error(self):
        """Test saving a match when the DynamoDB API fails."""
        # Arrange
        self.mock_table.put_item.side_effect = Exception("DynamoDB Error")
        match_data = {"match_id": "m-123", "person_id": "p-123"}

        # Act
        result = self.dynamodb_client.save_match(match_data)

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "DynamoDB Error")


    def test_query_matches_by_person_success(self):
        """Test successfully querying matches for a person."""
        # Arrange
        person_id = "p-123"
        expected_items = [{"match_id": "m-1"}, {"match_id": "m-2"}]
        self.mock_table.query.return_value = {"Items": expected_items}

        # Act
        result = self.dynamodb_client.query_matches_by_person(person_id, limit=10)

        # Assert
        self.assertEqual(result, expected_items)
        self.mock_dynamodb_resource.Table.assert_called_with(self.matches_table)
        self.mock_table.query.assert_called_once_with(
            IndexName="person_id-index",
            KeyConditionExpression="person_id = :pid",
            ExpressionAttributeValues={":pid": person_id},
            Limit=10,
            ScanIndexForward=False,
        )

    def test_query_matches_by_person_api_error(self):
        """Test querying matches when the DynamoDB API fails."""
        # Arrange
        self.mock_table.query.side_effect = Exception("DynamoDB Error")

        # Act
        result = self.dynamodb_client.query_matches_by_person("p-error")

        # Assert
        self.assertEqual(result, [])


    def test_delete_person_success(self):
        """Test successfully deleting a person."""
        # Arrange
        person_id = "p-123"

        # Act
        result = self.dynamodb_client.delete_person(person_id)

        # Assert
        self.assertTrue(result["success"])
        self.mock_dynamodb_resource.Table.assert_called_with(self.people_table)
        self.mock_table.delete_item.assert_called_once_with(Key={"person_id": person_id})

    def test_delete_person_api_error(self):
        """Test deleting a person when the DynamoDB API fails."""
        # Arrange
        self.mock_table.delete_item.side_effect = Exception("DynamoDB Error")

        # Act
        result = self.dynamodb_client.delete_person("p-error")

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "DynamoDB Error")


    def test_check_health_success(self):
        """Test successful health check."""
        # Arrange
        self.mock_table.table_status = "ACTIVE"

        # Act
        result = self.dynamodb_client.check_health()

        # Assert
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["table_status"], "ACTIVE")
        self.mock_table.load.assert_called_once()

    def test_check_health_api_error(self):
        """Test health check when the DynamoDB API fails."""
        # Arrange
        self.mock_table.load.side_effect = Exception("DynamoDB Error")

        # Act
        result = self.dynamodb_client.check_health()

        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "DynamoDB Error")

    def test_check_health_disabled(self):
        """Test health check when the client is disabled."""
        # Arrange
        client = DynamoDBClient(
            region=self.region,
            people_table=self.people_table,
            embeddings_table=self.embeddings_table,
            matches_table=self.matches_table,
            enabled=False,
        )

        # Act
        result = client.check_health()

        # Assert
        self.assertEqual(result["status"], "disabled")


if __name__ == "__main__":
    unittest.main()

