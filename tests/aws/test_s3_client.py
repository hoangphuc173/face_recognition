"""
Unit tests for the S3Client.
"""

import unittest
from unittest.mock import MagicMock, patch

from aws.backend.aws.s3_client import S3Client


class TestS3Client(unittest.TestCase):
    """Test suite for S3Client."""

    @patch("aws.backend.aws.s3_client.boto3")
    def setUp(self, mock_boto3):
        """Set up a mock S3 client before each test."""
        self.mock_s3_client = MagicMock()
        mock_boto3.client.return_value = self.mock_s3_client

        self.bucket_name = "test-bucket"
        self.region = "us-west-2"

        self.s3_client = S3Client(
            bucket_name=self.bucket_name, region=self.region, enabled=True
        )

    def test_init_success(self):
        """Test successful initialization."""
        self.assertTrue(self.s3_client.enabled)
        self.assertIsNotNone(self.s3_client.client)

    def test_init_disabled(self):
        """Test initialization when disabled."""
        client = S3Client(bucket_name=self.bucket_name, region=self.region, enabled=False)
        self.assertFalse(client.enabled)
        self.assertIsNone(client.client)

    def test_upload_file_success(self):
        """Test successfully uploading a file."""
        # Arrange
        local_path = "/tmp/test.jpg"
        s3_key = "uploads/test.jpg"

        # Act
        result = self.s3_client.upload_file(local_path=local_path, s3_key=s3_key)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["s3_url"], f"s3://{self.bucket_name}/{s3_key}")
        self.mock_s3_client.upload_file.assert_called_once_with(
            Filename=local_path,
            Bucket=self.bucket_name,
            Key=s3_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )

    def test_upload_file_api_error(self):
        """Test file upload when S3 API fails."""
        # Arrange
        self.mock_s3_client.upload_file.side_effect = Exception("S3 Error")

        # Act
        result = self.s3_client.upload_file(local_path="/tmp/file", s3_key="key")

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "S3 Error")


    def test_upload_bytes_success(self):
        """Test successfully uploading bytes."""
        # Arrange
        data = b"some-byte-data"
        s3_key = "uploads/data.bin"

        # Act
        result = self.s3_client.upload_bytes(data=data, s3_key=s3_key, content_type="application/octet-stream")

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["s3_url"], f"s3://{self.bucket_name}/{s3_key}")
        self.mock_s3_client.put_object.assert_called_once_with(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=data,
            ContentType="application/octet-stream"
        )

    def test_upload_bytes_api_error(self):
        """Test bytes upload when S3 API fails."""
        # Arrange
        self.mock_s3_client.put_object.side_effect = Exception("S3 Error")

        # Act
        result = self.s3_client.upload_bytes(data=b"data", s3_key="key")

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "S3 Error")


    @patch("aws.backend.aws.s3_client.Path")
    def test_download_image_success(self, mock_path):
        """Test successfully downloading an image."""
        # Arrange
        s3_key = "downloads/image.jpg"
        local_path = "/tmp/image.jpg"

        # Act
        result = self.s3_client.download_image(s3_key=s3_key, local_path=local_path)

        # Assert
        self.assertTrue(result["success"])
        mock_path.assert_called_with(local_path)
        mock_path.return_value.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        self.mock_s3_client.download_file.assert_called_once_with(
            Bucket=self.bucket_name, Key=s3_key, Filename=local_path
        )

    def test_download_image_api_error(self):
        """Test image download when S3 API fails."""
        # Arrange
        self.mock_s3_client.download_file.side_effect = Exception("S3 Error")

        # Act
        result = self.s3_client.download_image(s3_key="key", local_path="/path")

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "S3 Error")


    def test_delete_image_success(self):
        """Test successfully deleting an image."""
        # Arrange
        s3_key = "uploads/to-delete.jpg"

        # Act
        result = self.s3_client.delete_image(s3_key=s3_key)

        # Assert
        self.assertTrue(result["success"])
        self.mock_s3_client.delete_object.assert_called_once_with(
            Bucket=self.bucket_name, Key=s3_key
        )

    def test_delete_image_api_error(self):
        """Test image deletion when S3 API fails."""
        # Arrange
        self.mock_s3_client.delete_object.side_effect = Exception("S3 Error")

        # Act
        result = self.s3_client.delete_image(s3_key="key")

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "S3 Error")


    def test_generate_presigned_url_success(self):
        """Test successfully generating a presigned URL."""
        # Arrange
        s3_key = "protected/image.jpg"
        expected_url = "https://s3.amazonaws.com/test-bucket/protected/image.jpg?AWSAccessKeyId=..."
        self.mock_s3_client.generate_presigned_url.return_value = expected_url

        # Act
        result = self.s3_client.generate_presigned_url(s3_key=s3_key, expiration=900)

        # Assert
        self.assertEqual(result, expected_url)
        self.mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": s3_key},
            ExpiresIn=900,
        )

    def test_generate_presigned_url_api_error(self):
        """Test presigned URL generation when S3 API fails."""
        # Arrange
        self.mock_s3_client.generate_presigned_url.side_effect = Exception("S3 Error")

        # Act
        result = self.s3_client.generate_presigned_url(s3_key="key")

        # Assert
        self.assertIsNone(result)


    def test_list_images_success(self):
        """Test successfully listing images."""
        # Arrange
        prefix = "enrollments/"
        expected_keys = ["enrollments/1.jpg", "enrollments/2.jpg"]
        self.mock_s3_client.list_objects_v2.return_value = {
            "Contents": [{"Key": "enrollments/1.jpg"}, {"Key": "enrollments/2.jpg"}]
        }

        # Act
        result = self.s3_client.list_images(prefix=prefix)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["keys"], expected_keys)
        self.mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket=self.bucket_name, Prefix=prefix, MaxKeys=1000
        )

    def test_list_images_empty(self):
        """Test listing images when no objects are found."""
        # Arrange
        self.mock_s3_client.list_objects_v2.return_value = {}

        # Act
        result = self.s3_client.list_images(prefix="empty/")

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["keys"], [])

    def test_list_images_api_error(self):
        """Test listing images when S3 API fails."""
        # Arrange
        self.mock_s3_client.list_objects_v2.side_effect = Exception("S3 Error")

        # Act
        result = self.s3_client.list_images(prefix="error/")

        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "S3 Error")


if __name__ == "__main__":
    unittest.main()

