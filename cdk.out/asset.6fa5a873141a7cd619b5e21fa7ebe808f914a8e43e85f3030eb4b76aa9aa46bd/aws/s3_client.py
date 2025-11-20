"""S3 Client wrapper for image storage."""

import logging
import os
from pathlib import Path
from typing import Dict, Optional

import boto3

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for managing image storage."""

    def __init__(
        self,
        bucket_name: str,
        region: str,
        enabled: bool = True,
    ):
        """Initialize S3 client.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            enabled: Enable AWS operations (False for local-only mode)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.enabled = enabled and self.bucket_name is not None

        self.client = None
        if self.enabled:
            try:
                self.client = boto3.client("s3", region_name=region)
                logger.info(f"✅ S3 Client initialized: bucket={self.bucket_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize S3 client: {e}")
                self.enabled = False

    def upload_file(
        self,
        local_path: str,
        s3_key: str,
        metadata: Optional[Dict] = None,
        content_type: str = "image/jpeg",
    ) -> Dict:
        """Upload image to S3.

        Args:
            local_path: Local file path
            s3_key: S3 object key (e.g., "enrollments/person_id/image.jpg")
            metadata: Optional metadata to attach
            content_type: Content type (default: image/jpeg)

        Returns:
            Dict with success status and S3 URL
        """
        result = {"success": False, "s3_url": None, "error": None}

        if not self.enabled:
            result["error"] = "S3 not enabled"
            return result

        try:
            extra_args = {"ContentType": content_type}

            if metadata:
                extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}

            self.client.upload_file(
                Filename=local_path,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args,
            )

            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"✅ Uploaded to S3: {s3_url}")

            result["success"] = True
            result["s3_url"] = s3_url

        except Exception as e:
            logger.error(f"❌ S3 upload failed: {e}")
            result["error"] = str(e)

        return result

    def upload_bytes(
        self,
        data: bytes,
        s3_key: str,
        metadata: Optional[Dict] = None,
        content_type: str = "image/jpeg",
    ) -> Dict:
        """Upload bytes data to S3.

        Args:
            data: Bytes data to upload
            s3_key: S3 object key
            metadata: Optional metadata to attach
            content_type: Content type

        Returns:
            Dict with success status and S3 URL
        """
        result = {"success": False, "s3_url": None, "error": None}

        if not self.enabled:
            result["error"] = "S3 not enabled"
            return result

        try:
            extra_args = {"ContentType": content_type}

            if metadata:
                extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}

            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                **extra_args,
            )

            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"✅ Uploaded bytes to S3: {s3_url}")

            result["success"] = True
            result["s3_url"] = s3_url

        except Exception as e:
            logger.error(f"❌ S3 bytes upload failed: {e}")
            result["error"] = str(e)

        return result

    def download_image(self, s3_key: str, local_path: str) -> Dict:
        """Download image from S3.

        Args:
            s3_key: S3 object key
            local_path: Local destination path

        Returns:
            Dict with success status
        """
        result = {"success": False, "error": None}

        if not self.enabled:
            result["error"] = "S3 not enabled"
            return result

        try:
            # Create parent directories
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            self.client.download_file(
                Bucket=self.bucket_name, Key=s3_key, Filename=local_path
            )

            logger.info(f"✅ Downloaded from S3: {s3_key} -> {local_path}")
            result["success"] = True

        except Exception as e:
            logger.error(f"❌ S3 download failed: {e}")
            result["error"] = str(e)

        return result

    def delete_image(self, s3_key: str) -> Dict:
        """Delete image from S3.

        Args:
            s3_key: S3 object key

        Returns:
            Dict with success status
        """
        result = {"success": False, "error": None}

        if not self.enabled:
            result["error"] = "S3 not enabled"
            return result

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"✅ Deleted from S3: {s3_key}")
            result["success"] = True

        except Exception as e:
            logger.error(f"❌ S3 delete failed: {e}")
            result["error"] = str(e)

        return result

    def generate_presigned_url(
        self, s3_key: str, expiration: int = 3600
    ) -> Optional[str]:
        """Generate presigned URL for temporary access.

        Args:
            s3_key: S3 object key
            expiration: URL expiration in seconds (default: 1 hour)

        Returns:
            Presigned URL or None if failed
        """
        if not self.enabled:
            return None

        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return url

        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            return None

    def list_images(self, prefix: str = "", max_keys: int = 1000) -> Dict:
        """List images in S3 with given prefix.

        Args:
            prefix: S3 key prefix (e.g., "enrollments/person_123/")
            max_keys: Maximum number of keys to return

        Returns:
            Dict with list of S3 keys
        """
        result = {"success": False, "keys": [], "error": None}

        if not self.enabled:
            result["error"] = "S3 not enabled"
            return result

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=max_keys
            )

            if "Contents" in response:
                result["keys"] = [obj["Key"] for obj in response["Contents"]]

            result["success"] = True
            logger.info(
                f"✅ Listed {len(result['keys'])} objects with prefix: {prefix}"
            )

        except Exception as e:
            logger.error(f"❌ S3 list failed: {e}")
            result["error"] = str(e)

        return result
