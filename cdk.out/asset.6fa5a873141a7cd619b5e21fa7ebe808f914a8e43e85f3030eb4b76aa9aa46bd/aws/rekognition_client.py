"""Rekognition Client wrapper for face operations."""

import logging
import os
import boto3
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RekognitionClient:
    """Rekognition client for face detection, indexing, and search."""

    def __init__(
        self,
        collection_id: str,
        region: str,
        enabled: bool = True,
    ):
        """Initialize Rekognition client.

        Args:
            collection_id: Rekognition collection ID
            region: AWS region
            enabled: Enable AWS operations (False for local-only mode)
        """
        self.collection_id = collection_id
        self.region = region
        self.enabled = enabled and self.collection_id is not None

        self.client = None
        if self.enabled:
            try:
                self.client = boto3.client("rekognition", region_name=region)
                logger.info(
                    f"✅ Rekognition Client initialized: collection={self.collection_id}"
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Rekognition client: {e}")
                self.enabled = False

    def _read_image_bytes(self, image: bytes | str) -> bytes:
        """Read image bytes from path or return bytes directly."""
        if isinstance(image, str):
            with open(image, "rb") as f:
                return f.read()
        return image

    def detect_faces(self, image: bytes | str) -> Dict:
        """Detect faces in an image.

        Args:
            image: Image bytes or file path

        Returns:
            Dict with detected faces and their attributes
        """
        result = {"success": False, "faces": [], "error": None}

        if not self.enabled:
            result["error"] = "Rekognition not enabled"
            return result

        try:
            image_bytes = self._read_image_bytes(image)
            response = self.client.detect_faces(
                Image={"Bytes": image_bytes}, Attributes=["ALL"]
            )

            faces = []
            for face_detail in response.get("FaceDetails", []):
                faces.append(
                    {
                        "bounding_box": face_detail.get("BoundingBox"),
                        "confidence": face_detail.get("Confidence"),
                        "age_range": face_detail.get("AgeRange"),
                        "gender": face_detail.get("Gender"),
                        "emotions": face_detail.get("Emotions", []),
                        "quality": face_detail.get("Quality"),
                    }
                )

            result["success"] = True
            result["faces"] = faces
            logger.info(f"✅ Detected {len(faces)} faces with Rekognition")

        except Exception as e:
            logger.error(f"❌ Rekognition detect_faces failed: {e}")
            result["error"] = str(e)

        return result

    def index_face(
        self,
        image: bytes | str,
        external_image_id: str,
        max_faces: int = 1,
        quality_filter: str = "AUTO",
    ) -> Dict:
        """Index a face into the collection.

        Args:
            image: Image bytes or file path
            external_image_id: External ID (e.g., person_id)
            max_faces: Maximum faces to index (default: 1)
            quality_filter: Quality filter (AUTO, LOW, MEDIUM, HIGH, NONE)

        Returns:
            Dict with indexed face details
        """
        result = {
            "success": False,
            "face_id": None,
            "face_records": [],
            "error": None,
        }

        if not self.enabled:
            result["error"] = "Rekognition not enabled"
            return result

        try:
            image_bytes = self._read_image_bytes(image)
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={"Bytes": image_bytes},
                ExternalImageId=external_image_id,
                MaxFaces=max_faces,
                QualityFilter=quality_filter,
                DetectionAttributes=["ALL"],
            )

            face_records = response.get("FaceRecords", [])

            if face_records:
                result["success"] = True
                result["face_id"] = face_records[0]["Face"]["FaceId"]
                result["face_records"] = [
                    {
                        "face_id": record["Face"]["FaceId"],
                        "bounding_box": record["Face"]["BoundingBox"],
                        "confidence": record["Face"]["Confidence"],
                        "image_id": record["Face"]["ExternalImageId"],
                        "quality": record.get("FaceDetail", {}).get("Quality"),
                    }
                    for record in face_records
                ]
                logger.info(
                    f"✅ Indexed face in Rekognition: face_id={result['face_id']}, external_id={external_image_id}"
                )
            else:
                result["error"] = "No faces detected in image"
                logger.warning("⚠️ No faces detected for indexing")

        except Exception as e:
            logger.error(f"❌ Rekognition index_face failed: {e}")
            result["error"] = str(e)

        return result

    def search_faces(
        self,
        image: bytes | str,
        max_faces: int = 5,
        face_match_threshold: float = 70.0,
    ) -> Dict:
        """Search for matching faces in the collection.

        Args:
            image: Image bytes or file path containing face to search
            max_faces: Maximum results to return
            face_match_threshold: Similarity threshold (0-100, default 70)

        Returns:
            Dict with matched faces
        """
        result = {"success": False, "matches": [], "error": None}

        if not self.enabled:
            result["error"] = "Rekognition not enabled"
            return result

        try:
            image_bytes = self._read_image_bytes(image)
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={"Bytes": image_bytes},
                MaxFaces=max_faces,
                FaceMatchThreshold=face_match_threshold,
            )

            matches = []
            for face_match in response.get("FaceMatches", []):
                face = face_match["Face"]
                matches.append(
                    {
                        "face_id": face["FaceId"],
                        "external_image_id": face.get("ExternalImageId"),
                        "similarity": face_match["Similarity"],
                        "confidence": face.get("Confidence"),
                    }
                )

            result["success"] = True
            result["matches"] = matches
            logger.info(
                f"✅ Found {len(matches)} face matches with Rekognition (threshold={face_match_threshold})"
            )

        except self.client.exceptions.InvalidParameterException as e:
            # No face detected in image
            logger.warning(f"⚠️ No face detected for search: {e}")
            result["success"] = True  # Not an error, just no faces
            result["matches"] = []

        except Exception as e:
            logger.error(f"❌ Rekognition search_faces failed: {e}")
            result["error"] = str(e)

        return result

    def delete_faces(self, face_ids: List[str]) -> Dict:
        """Delete faces from the collection.

        Args:
            face_ids: List of face IDs to delete

        Returns:
            Dict with deletion results
        """
        result = {"success": False, "deleted_faces": [], "error": None}

        if not self.enabled:
            result["error"] = "Rekognition not enabled"
            return result

        try:
            response = self.client.delete_faces(
                CollectionId=self.collection_id, FaceIds=face_ids
            )

            result["success"] = True
            result["deleted_faces"] = response.get("DeletedFaces", [])
            logger.info(
                f"✅ Deleted {len(result['deleted_faces'])} faces from Rekognition"
            )

        except Exception as e:
            logger.error(f"❌ Rekognition delete_faces failed: {e}")
            result["error"] = str(e)

        return result

    def list_faces(self, max_results: int = 100) -> Dict:
        """List all faces in the collection.

        Args:
            max_results: Maximum results to return

        Returns:
            Dict with face list
        """
        result = {"success": False, "faces": [], "error": None}

        if not self.enabled:
            result["error"] = "Rekognition not enabled"
            return result

        try:
            response = self.client.list_faces(
                CollectionId=self.collection_id, MaxResults=max_results
            )

            faces = []
            for face in response.get("Faces", []):
                faces.append(
                    {
                        "face_id": face["FaceId"],
                        "external_image_id": face.get("ExternalImageId"),
                        "confidence": face.get("Confidence"),
                    }
                )

            result["success"] = True
            result["faces"] = faces
            logger.info(f"✅ Listed {len(faces)} faces from Rekognition")

        except Exception as e:
            logger.error(f"❌ Rekognition list_faces failed: {e}")
            result["error"] = str(e)

        return result

    def describe_collection(self) -> Dict:
        """Get collection statistics.

        Returns:
            Dict with collection details
        """
        result = {"success": False, "stats": {}, "error": None}

        if not self.enabled:
            result["error"] = "Rekognition not enabled"
            return result

        try:
            response = self.client.describe_collection(CollectionId=self.collection_id)

            result["success"] = True
            result["stats"] = {
                "face_count": response.get("FaceCount", 0),
                "face_model_version": response.get("FaceModelVersion"),
                "collection_arn": response.get("CollectionARN"),
                "creation_timestamp": response.get("CreationTimestamp"),
            }
            logger.info(
                f"✅ Collection stats: {result['stats']['face_count']} faces indexed"
            )

        except Exception as e:
            logger.error(f"❌ Rekognition describe_collection failed: {e}")
            result["error"] = str(e)

        return result

    def compare_faces(
        self,
        source_image: bytes | str,
        target_image: bytes | str,
        similarity_threshold: float = 70.0,
    ) -> Dict:
        """Compare two faces for similarity.

        Args:
            source_image: Source image bytes or file path
            target_image: Target image bytes or file path
            similarity_threshold: Minimum similarity (0-100)

        Returns:
            Dict with comparison results
        """
        result = {"success": False, "matches": [], "error": None}

        if not self.enabled:
            result["error"] = "Rekognition not enabled"
            return result

        try:
            source_bytes = self._read_image_bytes(source_image)
            target_bytes = self._read_image_bytes(target_image)
            response = self.client.compare_faces(
                SourceImage={"Bytes": source_bytes},
                TargetImage={"Bytes": target_bytes},
                SimilarityThreshold=similarity_threshold,
            )

            matches = []
            for face_match in response.get("FaceMatches", []):
                matches.append(
                    {
                        "similarity": face_match["Similarity"],
                        "face_confidence": face_match["Face"]["Confidence"],
                        "bounding_box": face_match["Face"]["BoundingBox"],
                    }
                )

            result["success"] = True
            result["matches"] = matches
            logger.info(f"✅ Face comparison: {len(matches)} matches found")

        except Exception as e:
            logger.error(f"❌ Rekognition compare_faces failed: {e}")
            result["error"] = str(e)

        return result
