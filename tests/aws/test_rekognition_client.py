"""
Unit tests for the RekognitionClient.
"""

import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from aws.backend.aws.rekognition_client import RekognitionClient


class TestRekognitionClient(unittest.TestCase):
    """Test suite for RekognitionClient."""

    @patch("aws.backend.aws.rekognition_client.boto3")
    def setUp(self, mock_boto3):
        """Set up a mock Rekognition client before each test."""
        self.mock_boto_client = MagicMock()
        # Configure the exception class on the mock client
        self.mock_boto_client.exceptions.InvalidParameterException = ClientError
        mock_boto3.client.return_value = self.mock_boto_client
        self.collection_id = "test-collection"
        self.region = "us-west-2"

        # Initialize the client to be tested
        self.rekognition_client = RekognitionClient(
            collection_id=self.collection_id, region=self.region, enabled=True
        )
        # self.rekognition_client.client should be our mock
        self.assertEqual(self.rekognition_client.client, self.mock_boto_client)

    def test_init_success(self):
        """Test successful initialization of the client."""
        self.assertTrue(self.rekognition_client.enabled)
        self.assertIsNotNone(self.rekognition_client.client)
        self.assertEqual(self.rekognition_client.collection_id, self.collection_id)

    def test_init_disabled(self):
        """Test that the client is disabled when enabled=False."""
        client = RekognitionClient(
            collection_id=self.collection_id, region=self.region, enabled=False
        )
        self.assertFalse(client.enabled)
        self.assertIsNone(client.client)

    def test_detect_faces_success(self):
        """Test successful face detection."""
        # Arrange
        fake_response = {
            "FaceDetails": [
                {
                    "BoundingBox": {"Width": 0.5, "Height": 0.5, "Left": 0.1, "Top": 0.1},
                    "Confidence": 99.9,
                }
            ]
        }
        self.mock_boto_client.detect_faces.return_value = fake_response
        image_bytes = b"dummy-image-bytes"

        # Act
        result = self.rekognition_client.detect_faces(image=image_bytes)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(len(result["faces"]), 1)
        self.assertEqual(result["faces"][0]["confidence"], 99.9)
        self.mock_boto_client.detect_faces.assert_called_once_with(
            Image={"Bytes": image_bytes}, Attributes=["ALL"]
        )

    def test_detect_faces_api_error(self):
        """Test face detection when the Rekognition API returns an error."""
        # Arrange
        self.mock_boto_client.detect_faces.side_effect = Exception("AWS API Error")
        image_bytes = b"dummy-image-bytes"

        # Act
        result = self.rekognition_client.detect_faces(image=image_bytes)

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(len(result["faces"]), 0)
        self.assertEqual(result["error"], "AWS API Error")


    def test_index_face_success(self):
        """Test successful face indexing."""
        # Arrange
        external_image_id = "person-123"
        face_id = "face-abc-def"
        fake_response = {
            "FaceRecords": [
                {
                    "Face": {
                        "FaceId": face_id,
                        "ExternalImageId": external_image_id,
                        "BoundingBox": {},
                        "Confidence": 99.0,
                    },
                    "FaceDetail": {"Quality": {"Sharpness": 95.0}},
                }
            ]
        }
        self.mock_boto_client.index_faces.return_value = fake_response
        image_bytes = b"dummy-image-bytes"

        # Act
        result = self.rekognition_client.index_face(
            image=image_bytes, external_image_id=external_image_id
        )

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["face_id"], face_id)
        self.assertEqual(len(result["face_records"]), 1)
        self.mock_boto_client.index_faces.assert_called_once()

    def test_index_face_no_faces_detected(self):
        """Test face indexing when no faces are detected in the image."""
        # Arrange
        fake_response = {"FaceRecords": []}
        self.mock_boto_client.index_faces.return_value = fake_response

        # Act
        result = self.rekognition_client.index_face(
            image=b"image", external_image_id="id"
        )

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["face_id"])
        self.assertEqual(result["error"], "No faces detected in image")

    def test_index_face_api_error(self):
        """Test face indexing when the Rekognition API returns an error."""
        # Arrange
        self.mock_boto_client.index_faces.side_effect = Exception("AWS Error")

        # Act
        result = self.rekognition_client.index_face(
            image=b"image", external_image_id="id"
        )

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "AWS Error")


    def test_search_faces_success(self):
        """Test successful face search with matches."""
        # Arrange
        fake_response = {
            "FaceMatches": [
                {
                    "Similarity": 99.0,
                    "Face": {
                        "FaceId": "face-1",
                        "ExternalImageId": "person-1",
                        "Confidence": 99.9,
                    },
                }
            ]
        }
        self.mock_boto_client.search_faces_by_image.return_value = fake_response

        # Act
        result = self.rekognition_client.search_faces(image=b"image")

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["face_id"], "face-1")

    def test_search_faces_no_match(self):
        """Test face search that returns no matches."""
        # Arrange
        fake_response = {"FaceMatches": []}
        self.mock_boto_client.search_faces_by_image.return_value = fake_response

        # Act
        result = self.rekognition_client.search_faces(image=b"image")

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(len(result["matches"]), 0)

    def test_search_faces_no_face_in_image(self):
        """Test face search when no face is detected in the source image."""
        # Arrange
        # Mock the specific exception for this case
        error_response = {
            "Error": {"Code": "InvalidParameterException", "Message": "No faces detected"}
        }
        operation_name = "SearchFacesByImage"
        side_effect = ClientError(error_response, operation_name)
        self.mock_boto_client.search_faces_by_image.side_effect = side_effect

        # Act
        result = self.rekognition_client.search_faces(image=b"image")

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(len(result["matches"]), 0)
        self.assertIsNone(result["error"])

    def test_search_faces_api_error(self):
        """Test face search when a general API error occurs."""
        # Arrange
        self.mock_boto_client.search_faces_by_image.side_effect = Exception("AWS Error")

        # Act
        result = self.rekognition_client.search_faces(image=b"image")

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "AWS Error")


    def test_delete_faces_success(self):
        """Test successful face deletion."""
        # Arrange
        face_ids_to_delete = ["face-1", "face-2"]
        fake_response = {"DeletedFaces": [{"FaceId": "face-1"}, {"FaceId": "face-2"}]}
        self.mock_boto_client.delete_faces.return_value = fake_response

        # Act
        result = self.rekognition_client.delete_faces(face_ids=face_ids_to_delete)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(len(result["deleted_faces"]), 2)
        self.mock_boto_client.delete_faces.assert_called_once_with(
            CollectionId=self.collection_id, FaceIds=face_ids_to_delete
        )

    def test_delete_faces_api_error(self):
        """Test face deletion when the Rekognition API returns an error."""
        # Arrange
        self.mock_boto_client.delete_faces.side_effect = Exception("AWS Error")

        # Act
        result = self.rekognition_client.delete_faces(face_ids=["face-1"])

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "AWS Error")


    def test_list_faces_success(self):
        """Test successfully listing faces in the collection."""
        # Arrange
        fake_response = {
            "Faces": [
                {"FaceId": "face-1", "ExternalImageId": "person-1"},
                {"FaceId": "face-2", "ExternalImageId": "person-2"},
            ]
        }
        self.mock_boto_client.list_faces.return_value = fake_response

        # Act
        result = self.rekognition_client.list_faces(max_results=10)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(len(result["faces"]), 2)
        self.assertEqual(result["faces"][0]["face_id"], "face-1")
        self.mock_boto_client.list_faces.assert_called_once_with(
            CollectionId=self.collection_id, MaxResults=10
        )

    def test_list_faces_api_error(self):
        """Test listing faces when the Rekognition API returns an error."""
        # Arrange
        self.mock_boto_client.list_faces.side_effect = Exception("AWS Error")

        # Act
        result = self.rekognition_client.list_faces()

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "AWS Error")


    def test_describe_collection_success(self):
        """Test successfully describing the collection."""
        # Arrange
        fake_response = {
            "FaceCount": 123,
            "FaceModelVersion": "5.0",
            "CollectionARN": "arn:aws:rekognition:us-west-2:123456789012:collection/test-collection",
        }
        self.mock_boto_client.describe_collection.return_value = fake_response

        # Act
        result = self.rekognition_client.describe_collection()

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["stats"]["face_count"], 123)
        self.assertEqual(result["stats"]["face_model_version"], "5.0")
        self.mock_boto_client.describe_collection.assert_called_once_with(
            CollectionId=self.collection_id
        )

    def test_describe_collection_api_error(self):
        """Test describing the collection when the API returns an error."""
        # Arrange
        self.mock_boto_client.describe_collection.side_effect = Exception("AWS Error")

        # Act
        result = self.rekognition_client.describe_collection()

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "AWS Error")


    def test_compare_faces_success(self):
        """Test successful face comparison with a match."""
        # Arrange
        fake_response = {
            "FaceMatches": [
                {
                    "Similarity": 95.5,
                    "Face": {"Confidence": 99.0, "BoundingBox": {}},
                }
            ]
        }
        self.mock_boto_client.compare_faces.return_value = fake_response

        # Act
        result = self.rekognition_client.compare_faces(
            source_image=b"source", target_image=b"target"
        )

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["similarity"], 95.5)
        self.mock_boto_client.compare_faces.assert_called_once()

    def test_compare_faces_no_match(self):
        """Test face comparison with no match found."""
        # Arrange
        fake_response = {"FaceMatches": []}
        self.mock_boto_client.compare_faces.return_value = fake_response

        # Act
        result = self.rekognition_client.compare_faces(
            source_image=b"source", target_image=b"target"
        )

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(len(result["matches"]), 0)

    def test_compare_faces_api_error(self):
        """Test face comparison when the API returns an error."""
        # Arrange
        self.mock_boto_client.compare_faces.side_effect = Exception("AWS Error")

        # Act
        result = self.rekognition_client.compare_faces(
            source_image=b"source", target_image=b"target"
        )

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "AWS Error")


if __name__ == "__main__":
    unittest.main()

