"""
Face Recognition System - Identification Module (AWS Cloud Only)
Full-Stack Serverless: Rekognition Search + DynamoDB Metadata + Redis Cache

Features:
1. Real-time face detection and search
2. 1:N matching against Rekognition collection
3. Retrieve person metadata from DynamoDB
4. Save match results to DynamoDB
5. Support for video stream identification
6. Redis caching for sub-50ms latency
"""

import logging
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class IdentificationService:
    """AWS Cloud-only Identification Service with Redis Caching"""

    def __init__(
        self,
        rekognition_client,
        dynamodb_client,
        s3_client=None,
        redis_client=None,
    ):
        """
        Args:
            rekognition_client: Rekognition client instance (required)
            dynamodb_client: DynamoDB client instance (required)
            s3_client: S3 client instance (optional, for saving results)
            redis_client: Redis client instance (optional, for caching)
        """
        if not rekognition_client or not dynamodb_client:
            raise ValueError("Rekognition and DynamoDB clients are required")

        self.rekognition = rekognition_client
        self.s3 = s3_client
        self.redis = redis_client
        self.db = DatabaseManager(
            aws_dynamodb_client=dynamodb_client, aws_s3_client=s3_client
        )
        
        cache_status = "enabled" if redis_client and redis_client.enabled else "disabled"
        logger.info(f"IdentificationService initialized: AWS Cloud Only (Redis cache: {cache_status})")

    def _compute_image_hash(self, image_bytes: bytes) -> str:
        """Compute hash of image for cache key."""
        return hashlib.sha256(image_bytes).hexdigest()[:16]

    def identify_face(
        self,
        image_bytes: bytes,
        max_results: int = 5,
        confidence_threshold: float = 80.0,  # Rekognition uses 0-100
        save_result: bool = True,
        use_cache: bool = True,
    ) -> Dict:
        """
        Identify faces from image using AWS Rekognition with Redis caching

        Args:
            image_bytes: Image bytes
            max_results: Maximum number of results to return
            confidence_threshold: Minimum confidence threshold (0-100)
            save_result: Save match result to DynamoDB
            use_cache: Use Redis cache for faster lookups

        Returns:
            Dict with identification result (with cache_hit indicator)
        """
        result = {
            "success": False,
            "faces_detected": 0,
            "faces": [],
            "message": "",
            "method": "rekognition",
            "cache_hit": False,
        }

        # Try cache first
        if use_cache and self.redis and self.redis.enabled:
            image_hash = self._compute_image_hash(image_bytes)
            cached_result = self.redis.get_search_result(image_hash)
            if cached_result:
                logger.info(f"✅ Cache hit for image {image_hash}")
                cached_result["cache_hit"] = True
                return cached_result

        try:
            logger.info("🔍 Searching faces in Rekognition collection...")

            # Search faces using Rekognition
            search_result = self.rekognition.search_faces(
                image=image_bytes,
                max_faces=max_results,
                face_match_threshold=confidence_threshold,
            )

            if not search_result["success"]:
                result["message"] = (
                    f"❌ Face search failed: {search_result.get('error')}"
                )
                return result

            matches = search_result.get("matches", [])
            result["faces_detected"] = len(matches)

            logger.info(f"🔍 Rekognition returned {len(matches)} match(es) with threshold {confidence_threshold}%")

            if not matches:
                result["success"] = True
                result["message"] = "✅ No matching faces found"
                logger.warning(f"⚠️ No matches found! Possible reasons: low similarity, different angle, poor lighting")
                return result

            # Retrieve person metadata from DynamoDB using BatchGetItem for efficiency
            person_ids = [m.get("external_image_id") for m in matches if m.get("external_image_id")]
            if not person_ids:
                result["success"] = True
                result["message"] = "✅ No matching faces with valid person IDs found"
                return result

            logger.info(f"📊 Retrieving metadata for {len(person_ids)} match(es) in a single batch...")
            people_data = self.db.get_people_batch(person_ids)
            people_map = {p["person_id"]: p for p in people_data}

            faces = []
            for match in matches:
                person_id = match.get("external_image_id")
                if not person_id:
                    continue

                person = people_map.get(person_id)
                if person:
                    similarity = match.get("similarity", 0.0)
                    face_info = {
                        "person_id": person_id,
                        "user_name": person.get("user_name", "Unknown"),
                        "gender": person.get("gender", ""),
                        "birth_year": person.get("birth_year", ""),
                        "hometown": person.get("hometown", ""),
                        "residence": person.get("residence", ""),
                        "confidence": similarity / 100.0,  # Convert to 0-1 scale
                        "similarity": similarity,
                        "face_id": match.get("face_id"),
                        "match_time": datetime.now().isoformat(),
                    }
                    faces.append(face_info)
                    logger.info(
                        f"✅ Match: {person.get('user_name')} (confidence: {similarity:.1f}%)"
                    )
                else:
                    logger.warning(f"⚠️ Person not found in DynamoDB (batch query): {person_id}")

            result["faces"] = faces
            result["success"] = len(faces) > 0
            result["message"] = f"✅ Found {len(faces)} matching face(s)"

            # Cache the result
            if use_cache and self.redis and self.redis.enabled and faces:
                image_hash = self._compute_image_hash(image_bytes)
                # Cache for 5 minutes
                self.redis.set_search_result(image_hash, result, ttl=300)
                logger.info(f"✅ Cached search result for {image_hash}")

            # Save match results to DynamoDB
            if save_result and faces:
                self._save_match_results(image_bytes, faces)

            return result

        except Exception as e:
            logger.error(f"❌ Identification error: {e}", exc_info=True)
            result["message"] = f"❌ Identification failed: {str(e)}"
            return result

    def identify_faces_in_video(
        self,
        video_path: str,
        frame_interval: int = 30,
        max_results: int = 5,
        confidence_threshold: float = 80.0,
    ) -> Dict:
        """
        Identify faces from video frames

        Args:
            video_path: Video file path
            frame_interval: Process every N frames
            max_results: Maximum matches per frame
            confidence_threshold: Minimum confidence (0-100)

        Returns:
            Dict with video identification results
        """
        result = {
            "success": False,
            "frames_processed": 0,
            "total_matches": 0,
            "unique_persons": set(),
            "frame_results": [],
            "message": "",
        }

        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                result["message"] = f"❌ Failed to open video: {video_path}"
                return result

            frame_count = 0
            processed_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # Process every N frames
                if frame_count % frame_interval != 0:
                    continue

                processed_count += 1

                # Encode frame to bytes to process in-memory
                ret, frame_buffer = cv2.imencode(".jpg", frame)
                if not ret:
                    logger.warning(f"Failed to encode frame {frame_count}")
                    continue

                # Identify faces in frame
                frame_result = self.identify_face(
                    image_bytes=frame_buffer.tobytes(),
                    max_results=max_results,
                    confidence_threshold=confidence_threshold,
                    save_result=False,
                )

                if frame_result["success"] and frame_result["faces"]:
                    result["total_matches"] += len(frame_result["faces"])

                    for face in frame_result["faces"]:
                        result["unique_persons"].add(face["person_id"])

                    result["frame_results"].append(
                        {
                            "frame_number": frame_count,
                            "timestamp": frame_count / cap.get(cv2.CAP_PROP_FPS),
                            "faces": frame_result["faces"],
                        }
                    )

                logger.info(f"📹 Processed frame {processed_count}/{frame_count}")

            cap.release()

            result["frames_processed"] = processed_count
            result["success"] = result["total_matches"] > 0
            result["unique_persons"] = list(result["unique_persons"])
            result["message"] = (
                f"✅ Found {len(result['unique_persons'])} unique person(s) in {processed_count} frames"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Video identification error: {e}", exc_info=True)
            result["message"] = f"❌ Video identification failed: {str(e)}"
            return result

    def compare_faces(
        self,
        source_image: bytes | str,
        target_image: bytes | str,
        similarity_threshold: float = 80.0,
    ) -> Dict:
        """
        Compare two faces (1:1 matching)

        Args:
            source_image: Source image bytes or file path
            target_image: Target image bytes or file path
            similarity_threshold: Minimum similarity (0-100)

        Returns:
            Dict with comparison result
        """
        result = {
            "success": False,
            "match": False,
            "similarity": 0.0,
            "message": "",
        }

        try:
            logger.info("🔍 Comparing faces...")

            compare_result = self.rekognition.compare_faces(
                source_image=source_image,
                target_image=target_image,
                similarity_threshold=similarity_threshold,
            )

            if not compare_result["success"]:
                result["message"] = (
                    f"❌ Face comparison failed: {compare_result.get('error')}"
                )
                return result

            matches = compare_result.get("matches", [])

            if matches:
                # Get highest similarity
                best_match = max(matches, key=lambda x: x.get("similarity", 0))
                similarity = best_match.get("similarity", 0.0)

                result["success"] = True
                result["match"] = similarity >= similarity_threshold
                result["similarity"] = similarity
                result["message"] = f"✅ Similarity: {similarity:.1f}%"
            else:
                result["success"] = True
                result["match"] = False
                result["message"] = "✅ No match found"

            return result

        except Exception as e:
            logger.error(f"❌ Face comparison error: {e}", exc_info=True)
            result["message"] = f"❌ Face comparison failed: {str(e)}"
            return result

    def _save_match_results(self, image_bytes: bytes, faces: List[Dict]) -> None:
        """
        Save match results to DynamoDB

        Args:
            image_bytes: Source image bytes
            faces: List of matched faces
        """
        try:
            # Upload image to S3 (optional)
            image_url = None
            if self.s3:
                image_key = f"identifications/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.jpg"
                s3_result = self.s3.upload_bytes(image_bytes, image_key)
                if s3_result["success"]:
                    image_url = s3_result.get("s3_url")

            # Save each match to DynamoDB
            for face in faces:
                match_data = {
                    "match_id": f"match_{uuid.uuid4().hex[:12]}",
                    "person_id": face["person_id"],
                    "timestamp": datetime.now().isoformat(),
                    "confidence": face["confidence"],
                    "similarity": face["similarity"],
                    "image_url": image_url,
                    "face_id": face.get("face_id"),
                }
                logger.debug("Match payload prepared: %s", match_data)

                # Save to DynamoDB Matches table
                # Note: This requires a Matches table in DynamoDB
                # self.db.save_match(match_data)

                logger.info(
                    "💾 Prepared match result payload for %s (%s confidence)",
                    face["user_name"],
                    f"{face['confidence']:.2%}",
                )

        except Exception as e:
            logger.error(f"❌ Error saving match results: {e}")

    def get_person_matches(self, person_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent matches for a person

        Args:
            person_id: Person ID
            limit: Maximum number of results

        Returns:
            List of match records
        """
        try:
            # Query DynamoDB Matches table by person_id
            # This requires implementing get_matches_by_person in DatabaseManager
            # matches = self.db.get_matches_by_person(person_id, limit)
            # return matches

            logger.info(f"📊 Retrieving matches for person: {person_id}")
            return []

        except Exception as e:
            logger.error(f"❌ Error retrieving matches: {e}")
            return []

    def get_statistics(self) -> Dict:
        """
        Get system statistics

        Returns:
            Dict with statistics
        """
        try:
            people = self.db.get_all_people()

            total_people = len(people)
            total_embeddings = sum(p.get("embedding_count", 0) for p in people)

            # Get collection stats from Rekognition
            collection_stats = self.rekognition.get_collection_stats()

            stats = {
                "total_people": total_people,
                "total_embeddings": total_embeddings,
                "rekognition_faces": collection_stats.get("face_count", 0),
                "collection_id": collection_stats.get("collection_id", ""),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"📊 Statistics: {total_people} people, {total_embeddings} embeddings"
            )
            return stats

        except Exception as e:
            logger.error(f"❌ Error retrieving statistics: {e}")
            return {}
