"""
Face Recognition System - Enrollment Module (AWS Cloud Only)
Full-Stack Serverless: Rekognition + DynamoDB + S3

Features:
1. Upload images to S3
2. Index faces in Rekognition collection
3. Store metadata in DynamoDB
4. High-quality reference images
5. Real-time face quality validation with anti-spoofing
"""

import logging
import uuid
from typing import Dict, List

from .database_manager import DatabaseManager
from .auth_utils import is_admin

logger = logging.getLogger(__name__)

# Import quality validator
try:
    from ..utils.image_quality import get_validator
    QUALITY_VALIDATOR_AVAILABLE = True
except ImportError:
    QUALITY_VALIDATOR_AVAILABLE = False
    logger.warning("⚠️ Image quality validator not available")





class EnrollmentService:
    """AWS Cloud-only Enrollment Service"""

    def __init__(
        self,
        s3_client,
        rekognition_client,
        dynamodb_client,
    ):
        """
        Args:
            s3_client: S3 client instance (required)
            rekognition_client: Rekognition client instance (required)
            dynamodb_client: DynamoDB client instance (required)
        """
        if not s3_client or not rekognition_client or not dynamodb_client:
            raise ValueError("All AWS clients (S3, Rekognition, DynamoDB) are required")

        self.s3 = s3_client
        self.rekognition = rekognition_client
        self.db = DatabaseManager(
            aws_dynamodb_client=dynamodb_client, aws_s3_client=s3_client
        )

        logger.info("EnrollmentService initialized: AWS Cloud Only")

    def enroll_face(
        self,
        image_bytes: bytes,
        user_name: str,
        gender: str = "",
        birth_year: str = "",
        hometown: str = "",
        residence: str = "",
        check_duplicate: bool = True,
        duplicate_threshold: float = 95.0,  # Rekognition uses 0-100
        event: Dict = None,  # Optional for backward compatibility
    ) -> Dict:
        """
        Enroll new face into the system (AWS Rekognition + S3 + DynamoDB)

        Args:
            image_path: Image file path
            user_name: User name (required)
            gender: Gender
            birth_year: Birth year
            hometown: Hometown
            residence: Current residence
            check_duplicate: Check for duplicates in collection
            duplicate_threshold: Similarity threshold (0-100)

        Returns:
            Dict with enrollment result
        """
        # Authorization check removed - open access
        
        result = {
            "success": False,
            "user_name": user_name,
            "person_id": None,
            "face_id": None,
            "message": "",
            "duplicate_found": False,
            "duplicate_info": None,
        }

        # Check if AWS services are configured
        try:
            if not self.s3.bucket_name or not self.rekognition.collection_id:
                result["message"] = "⚠️ AWS services not configured. Please set AWS credentials and bucket/collection names in .env file."
                logger.warning("AWS services not configured - S3 bucket or Rekognition collection missing")
                return result
        except Exception as e:
            result["message"] = f"⚠️ AWS configuration error: {str(e)}"
            logger.error(f"AWS configuration check failed: {e}")
            return result

        try:
            # Step 0: Validate image quality (anti-spoofing)
            if QUALITY_VALIDATOR_AVAILABLE:
                logger.info("🔍 Validating image quality...")
                validator = get_validator()
                
                # First detect face to get face details
                detect_result = self.rekognition.detect_faces(image_bytes)
                
                face_details = None
                if detect_result.get("success") and detect_result.get("faces"):
                    face_details = detect_result["faces"][0]
                
                quality_result = validator.validate_image_quality(
                    image_bytes, 
                    face_details
                )
                
                if not quality_result["valid"]:
                    result["message"] = f"⚠️ Image quality validation failed: {', '.join(quality_result['warnings'])}"
                    result["quality_check"] = quality_result
                    logger.warning(result["message"])
                    return result
                
                logger.info("✅ Image quality validation passed")
                result["quality_check"] = quality_result
            
            # Step 1: Check duplicate (optional)
            if check_duplicate:
                logger.info("🔍 Checking for duplicate faces...")
                duplicate_result = self._check_duplicate(
                    image_bytes, duplicate_threshold
                )

                if duplicate_result["duplicate_found"]:
                    result["duplicate_found"] = True
                    result["duplicate_info"] = duplicate_result["matches"]
                    result["message"] = "⚠️ Found duplicate faces in collection"
                    logger.warning(
                        f"Found {len(duplicate_result['matches'])} duplicate(s)"
                    )
                    return result

            # Step 2: Upload image to S3
            logger.info("📤 Uploading image to S3...")
            image_key = f"enrollments/{user_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}.jpg"
            s3_result = self.s3.upload_bytes(image_bytes, image_key)

            if not s3_result["success"]:
                result["message"] = (
                    f"❌ Failed to upload image: {s3_result.get('error')}"
                )
                return result

            image_url = s3_result["s3_url"]
            logger.info(f"✅ Image uploaded: {image_url}")

            # Step 3: Create person in DynamoDB first
            logger.info("💾 Creating person profile in DynamoDB...")
            person_id = f"person_{uuid.uuid4().hex[:12]}"

            person_result = self.db.create_person(
                user_name=user_name,
                gender=gender,
                birth_year=birth_year,
                hometown=hometown,
                residence=residence,
                person_id=person_id,
            )

            if not person_result["success"]:
                result["message"] = (
                    f"❌ Failed to create person: {person_result.get('message')}"
                )
                return result

            # Step 4: Index face in Rekognition
            logger.info("🤖 Indexing face in Rekognition collection...")
            rekog_result = self.rekognition.index_face(
                image=image_bytes,
                external_image_id=person_id,
                max_faces=1,
            )

            if not rekog_result["success"]:
                # Rollback: Delete person from DynamoDB
                self.db.delete_person(person_id)
                result["message"] = (
                    f"❌ Failed to index face: {rekog_result.get('error')}"
                )
                return result

            face_id = rekog_result["face_id"]
            quality_score = rekog_result.get("quality_score", 0.0)
            logger.info(f"✅ Face indexed: {face_id} (quality: {quality_score:.2f})")

            # Step 5: Save embedding metadata to DynamoDB
            logger.info("💾 Saving embedding metadata...")
            embedding_result = self.db.add_embedding(
                person_id=person_id,
                face_id=face_id,
                image_url=image_url,
                quality_score=quality_score,
            )

            if not embedding_result["success"]:
                logger.warning(
                    f"⚠️ Failed to save embedding metadata: {embedding_result.get('error')}"
                )
                # Continue anyway, face is already indexed

            # Success!
            result["success"] = True
            result["person_id"] = person_id
            result["face_id"] = face_id
            result["image_url"] = image_url
            result["quality_score"] = quality_score
            result["message"] = (
                f"✅ Successfully enrolled: {user_name} (ID: {person_id})"
            )

            logger.info(f"✅ Enrollment complete: {user_name} -> {person_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Enrollment error: {e}", exc_info=True)
            result["message"] = f"❌ Enrollment failed: {str(e)}"
            return result

    def _check_duplicate(self, image_bytes: bytes, threshold: float) -> Dict:
        """
        Check if face already exists in Rekognition collection

        Args:
            image_bytes: Image bytes
            threshold: Similarity threshold (0-100)

        Returns:
            Dict with duplicate check result
        """
        try:
            search_result = self.rekognition.search_faces(
                image=image_bytes,
                max_faces=5,
                face_match_threshold=threshold,
            )

            if search_result["success"] and search_result["matches"]:
                # Found potential duplicates
                matches = []
                for match in search_result["matches"]:
                    person_id = match.get("external_image_id")
                    if person_id:
                        person = self.db.get_person(person_id)
                        if person:
                            matches.append(
                                {
                                    "person_id": person_id,
                                    "user_name": person.get("user_name", "Unknown"),
                                    "similarity": match.get("similarity", 0.0),
                                    "face_id": match.get("face_id"),
                                }
                            )

                return {
                    "duplicate_found": len(matches) > 0,
                    "matches": matches,
                }

            return {"duplicate_found": False, "matches": []}

        except Exception as e:
            logger.error(f"❌ Duplicate check error: {e}")
            return {"duplicate_found": False, "matches": []}

    def enroll_multiple_faces(
        self,
        event: Dict,
        image_bytes_list: List[bytes],
        user_name: str,
        gender: str = "",
        birth_year: str = "",
        hometown: str = "",
        residence: str = "",
    ) -> Dict:
        """
        Enroll multiple faces for the same person

        Args:
            event: Lambda event for authorization
            image_bytes_list: List of image bytes
            user_name: User name
            gender: Gender
            birth_year: Birth year
            hometown: Hometown
            residence: Current residence

        Returns:
            Dict with enrollment results
        """
        # Step 0: Authorization Check
        if not is_admin(event):
            logger.error("🚫 Unauthorized: User is not in the admin group.")
            return {
                "success": False,
                "message": "🚫 Permission denied. Admin access required.",
                "user_name": user_name,
            }

        results = {
            "success": False,
            "user_name": user_name,
            "person_id": None,
            "total_images": len(image_bytes_list),
            "enrolled_count": 0,
            "failed_count": 0,
            "results": [],
        }

        # Create person first (only once)
        person_id = f"person_{uuid.uuid4().hex[:12]}"
        person_result = self.db.create_person(
            user_name=user_name,
            gender=gender,
            birth_year=birth_year,
            hometown=hometown,
            residence=residence,
            person_id=person_id,
        )

        if not person_result["success"]:
            results["message"] = "❌ Failed to create person profile"
            return results

        results["person_id"] = person_id

        # Enroll each face
        for idx, image_bytes in enumerate(image_bytes_list, 1):
            logger.info("📸 Enrolling face %s/%s...", idx, len(image_bytes_list))

            try:
                # Upload to S3
                image_key = (
                    f"enrollments/{person_id}/face_{idx}_{uuid.uuid4().hex[:8]}.jpg"
                )
                s3_result = self.s3.upload_bytes(image_bytes, image_key)

                if not s3_result["success"]:
                    results["failed_count"] += 1
                    results["results"].append(
                        {
                            "image_index": idx,
                            "success": False,
                            "error": "S3 upload failed",
                        }
                    )
                    continue

                # Index face in Rekognition
                rekog_result = self.rekognition.index_face(
                    image=image_bytes,
                    external_image_id=person_id,
                    max_faces=1,
                )

                if not rekog_result["success"]:
                    results["failed_count"] += 1
                    results["results"].append(
                        {
                            "image_index": idx,
                            "success": False,
                            "error": "Rekognition indexing failed",
                        }
                    )
                    continue

                # Save embedding metadata
                self.db.add_embedding(
                    person_id=person_id,
                    face_id=rekog_result["face_id"],
                    image_url=s3_result["url"],
                    quality_score=rekog_result.get("quality_score", 0.0),
                )

                results["enrolled_count"] += 1
                results["results"].append(
                    {
                        "image_index": idx,
                        "success": True,
                        "face_id": rekog_result["face_id"],
                    }
                )

            except Exception as e:
                logger.error(f"❌ Error enrolling face {idx}: {e}")
                results["failed_count"] += 1
                results["results"].append(
                    {
                        "image_index": idx,
                        "success": False,
                        "error": str(e),
                    }
                )

        results["success"] = results["enrolled_count"] > 0
        results["message"] = (
            f"✅ Enrolled {results['enrolled_count']}/{results['total_images']} faces"
        )

        return results
