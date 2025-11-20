"""
Unit tests for the IdentificationService.
"""

import unittest
from unittest.mock import MagicMock, patch

from aws.backend.core.identification_service import IdentificationService


class TestIdentificationService(unittest.TestCase):
    """Test suite for IdentificationService."""

    def setUp(self):
        """Set up mock clients for each test."""
        self.mock_rekognition_client = MagicMock()
        self.mock_dynamodb_client = MagicMock()
        self.mock_s3_client = MagicMock()

    def test_init_success(self):
        """Test successful initialization."""
        try:
            IdentificationService(
                rekognition_client=self.mock_rekognition_client,
                dynamodb_client=self.mock_dynamodb_client,
                s3_client=self.mock_s3_client,
            )
        except ValueError:
            self.fail("IdentificationService raised ValueError unexpectedly!")

    def test_init_missing_clients(self):
        """Test initialization fails if required clients are missing."""
        with self.assertRaises(ValueError):
            IdentificationService(rekognition_client=None, dynamodb_client=None)

        with self.assertRaises(ValueError):
            IdentificationService(
                rekognition_client=self.mock_rekognition_client, dynamodb_client=None
            )


    @patch("aws.backend.core.identification_service.DatabaseManager")
    def test_identify_face_success(self, MockDatabaseManager):
        """Test successful face identification with one match."""
        # Arrange
        mock_db_instance = MockDatabaseManager.return_value
        mock_db_instance.get_person.return_value = {
            "person_id": "person_123",
            "user_name": "John Doe",
            "gender": "Male",
            "birth_year": "1990",
            "hometown": "CityA",
            "residence": "CityB",
        }

        self.mock_rekognition_client.search_faces.return_value = {
            "success": True,
            "matches": [
                {
                    "external_image_id": "person_123",
                    "face_id": "face_abc_def",
                    "similarity": 99.5,
                }
            ],
        }

        service = IdentificationService(
            rekognition_client=self.mock_rekognition_client,
            dynamodb_client=self.mock_dynamodb_client,
            s3_client=self.mock_s3_client,
        )
        # We need to re-assign the mocked db manager to the instance
        service.db = mock_db_instance

        image_bytes = b"fake_image_data"

        # Act
        result = service.identify_face(image_bytes=image_bytes, save_result=True)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["faces_detected"], 1)
        self.assertEqual(len(result["faces"]), 1)
        self.assertEqual(result["message"], "✅ Found 1 matching face(s)")

        face = result["faces"][0]
        self.assertEqual(face["person_id"], "person_123")
        self.assertEqual(face["user_name"], "John Doe")
        self.assertEqual(face["similarity"], 99.5)
        self.assertAlmostEqual(face["confidence"], 0.995)

        # Verify mocks were called
        self.mock_rekognition_client.search_faces.assert_called_once_with(
            image_bytes=image_bytes, max_faces=5, face_match_threshold=80.0
        )
        mock_db_instance.get_person.assert_called_once_with("person_123")


    @patch("aws.backend.core.identification_service.DatabaseManager")
    def test_identify_face_no_match(self, MockDatabaseManager):
        """Test face identification when no matches are found."""
        # Arrange
        mock_db_instance = MockDatabaseManager.return_value
        self.mock_rekognition_client.search_faces.return_value = {
            "success": True,
            "matches": [],
        }

        service = IdentificationService(
            rekognition_client=self.mock_rekognition_client,
            dynamodb_client=self.mock_dynamodb_client,
        )
        service.db = mock_db_instance

        image_bytes = b"fake_image_data"

        # Act
        result = service.identify_face(image_bytes=image_bytes)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["faces_detected"], 0)
        self.assertEqual(len(result["faces"]), 0)
        self.assertEqual(result["message"], "✅ No matching faces found")

        # Verify mocks were called
        self.mock_rekognition_client.search_faces.assert_called_once()
        mock_db_instance.get_person.assert_not_called()


    def test_identify_face_rekognition_error(self):
        """Test face identification when Rekognition search fails."""
        # Arrange
        self.mock_rekognition_client.search_faces.return_value = {
            "success": False,
            "error": "Something went wrong",
        }

        service = IdentificationService(
            rekognition_client=self.mock_rekognition_client,
            dynamodb_client=self.mock_dynamodb_client,
        )

        # Act
        result = service.identify_face(image_bytes=b"fake_image_data")

        # Assert
        self.assertFalse(result["success"])
        self.assertIn("Face search failed", result["message"])
        self.mock_rekognition_client.search_faces.assert_called_once()


    @patch("aws.backend.core.identification_service.DatabaseManager")
    def test_identify_face_person_not_found_in_db(self, MockDatabaseManager):
        """Test identification when a matched person is not in the database."""
        # Arrange
        mock_db_instance = MockDatabaseManager.return_value
        mock_db_instance.get_person.return_value = None  # Person not found

        self.mock_rekognition_client.search_faces.return_value = {
            "success": True,
            "matches": [
                {
                    "external_image_id": "unknown_person_456",
                    "face_id": "face_xyz_789",
                    "similarity": 95.0,
                }
            ],
        }

        service = IdentificationService(
            rekognition_client=self.mock_rekognition_client,
            dynamodb_client=self.mock_dynamodb_client,
        )
        service.db = mock_db_instance

        # Act
        result = service.identify_face(image_bytes=b"fake_image_data")

        # Assert
        self.assertFalse(result["success"])  # No valid faces were found
        self.assertEqual(result["faces_detected"], 1)
        self.assertEqual(len(result["faces"]), 0)  # The list of faces should be empty
        self.assertIn("Found 0 matching face(s)", result["message"])

        # Verify mocks
        mock_db_instance.get_person.assert_called_once_with("unknown_person_456")


    def test_compare_faces_success(self):
        """Test successful 1:1 face comparison."""
        # Arrange
        self.mock_rekognition_client.compare_faces.return_value = {
            "success": True,
            "matches": [{"similarity": 92.5}],
        }

        service = IdentificationService(
            rekognition_client=self.mock_rekognition_client,
            dynamodb_client=self.mock_dynamodb_client,
        )

        source_img = b"source_image"
        target_img = b"target_image"

        # Act
        result = service.compare_faces(source_img, target_img)

        # Assert
        self.assertTrue(result["success"])
        self.assertTrue(result["match"])
        self.assertEqual(result["similarity"], 92.5)
        self.assertIn("Similarity: 92.5%", result["message"])
        self.mock_rekognition_client.compare_faces.assert_called_once_with(
            source_image=source_img, target_image=target_img, similarity_threshold=80.0
        )


    def test_compare_faces_no_match(self):
        """Test 1:1 face comparison when no match is found."""
        # Arrange
        self.mock_rekognition_client.compare_faces.return_value = {
            "success": True,
            "matches": [],
        }

        service = IdentificationService(
            rekognition_client=self.mock_rekognition_client,
            dynamodb_client=self.mock_dynamodb_client,
        )

        # Act
        result = service.compare_faces(b"source", b"target")

        # Assert
        self.assertTrue(result["success"])
        self.assertFalse(result["match"])
        self.assertEqual(result["similarity"], 0.0)
        self.assertEqual(result["message"], "✅ No match found")
        self.mock_rekognition_client.compare_faces.assert_called_once()


    def test_compare_faces_rekognition_error(self):
        """Test 1:1 face comparison when Rekognition fails."""
        # Arrange
        self.mock_rekognition_client.compare_faces.return_value = {
            "success": False,
            "error": "AWS error",
        }

        service = IdentificationService(
            rekognition_client=self.mock_rekognition_client,
            dynamodb_client=self.mock_dynamodb_client,
        )

        # Act
        result = service.compare_faces(b"source", b"target")

        # Assert
        self.assertFalse(result["success"])
        self.assertFalse(result["match"])
        self.assertIn("Face comparison failed", result["message"])
        self.mock_rekognition_client.compare_faces.assert_called_once()


    @patch("aws.backend.core.identification_service.DatabaseManager")
    def test_get_statistics(self, MockDatabaseManager):
        """Test retrieving system statistics."""
        # Arrange
        mock_db_instance = MockDatabaseManager.return_value
        mock_db_instance.get_all_people.return_value = [
            {"person_id": "p1", "embedding_count": 2},
            {"person_id": "p2", "embedding_count": 3},
        ]

        self.mock_rekognition_client.get_collection_stats.return_value = {
            "face_count": 10,
            "collection_id": "test_collection",
        }

        service = IdentificationService(
            rekognition_client=self.mock_rekognition_client,
            dynamodb_client=self.mock_dynamodb_client,
        )
        service.db = mock_db_instance

        # Act
        stats = service.get_statistics()

        # Assert
        self.assertEqual(stats["total_people"], 2)
        self.assertEqual(stats["total_embeddings"], 5)
        self.assertEqual(stats["rekognition_faces"], 10)
        self.assertEqual(stats["collection_id"], "test_collection")

        # Verify mocks
        mock_db_instance.get_all_people.assert_called_once()
        self.mock_rekognition_client.get_collection_stats.assert_called_once()


if __name__ == "__main__":
    unittest.main()
