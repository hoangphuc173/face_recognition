"""
Database Manager - AWS Cloud Only (DynamoDB + S3 + Rekognition)
Full-Stack Serverless Architecture

AWS Services:
- DynamoDB: People table (metadata)
- DynamoDB: Embeddings table (face vectors)
- S3: Image storage
- Rekognition: Face collection
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from .auth_utils import is_admin

logger = logging.getLogger(__name__)


class DatabaseManager:
    """AWS Cloud-only Database Manager for Face Recognition"""

    def __init__(self, aws_dynamodb_client, aws_s3_client=None):
        """
        Args:
            aws_dynamodb_client: DynamoDB client instance (required)
            aws_s3_client: S3 client instance (optional)
        """
        if not aws_dynamodb_client:
            raise ValueError("AWS DynamoDB client is required for cloud-only mode")

        self.dynamodb = aws_dynamodb_client
        self.s3 = aws_s3_client

        logger.info("DatabaseManager initialized: AWS Cloud Only")

    def create_person(
        self,
        user_name: str,
        gender: str = "",
        birth_year: str = "",
        hometown: str = "",
        residence: str = "",
        person_id: Optional[str] = None,
    ) -> Dict:
        """
        Create new person profile in DynamoDB

        Args:
            user_name: Person name (required)
            gender: Gender
            birth_year: Birth year
            hometown: Hometown
            residence: Current residence
            person_id: Person ID (auto-generated if not provided)

        Returns:
            Dict with creation result
        """
        # Generate person_id if not provided
        if not person_id:
            import uuid

            person_id = f"person_{uuid.uuid4().hex[:12]}"

        # Create person data
        person_data = {
            "person_id": person_id,
            "user_name": user_name,
            "gender": gender,
            "birth_year": birth_year,
            "hometown": hometown,
            "residence": residence,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "embedding_count": 0,
        }

        # Save to DynamoDB
        result = self.dynamodb.save_person(person_data)

        if result["success"]:
            logger.info(f"✅ Created person in DynamoDB: {person_id}")
            return {
                "success": True,
                "person_id": person_id,
                "message": f"✅ Created profile: {user_name} (ID: {person_id})",
            }
        else:
            logger.error(f"❌ Failed to create person: {result.get('error')}")
            return {
                "success": False,
                "message": f"❌ Failed to create profile: {result.get('error')}",
            }

    def get_person(self, person_id: str) -> Optional[Dict]:
        """
        Get person info from DynamoDB

        Args:
            person_id: Person ID

        Returns:
            Person data dict or None
        """
        # dynamodb.get_person() returns Optional[Dict] directly
        return self.dynamodb.get_person(person_id)

    def get_people_batch(self, person_ids: List[str]) -> List[Dict]:
        """Get multiple people by a list of IDs from DynamoDB.

        Args:
            person_ids: A list of person IDs.

        Returns:
            A list of person data dicts.
        """
        result = self.dynamodb.get_people_batch(person_ids)
        if result["success"]:
            return result["people"]
        return []

    def get_all_people(self) -> List[Dict]:
        """
        Get all people from DynamoDB

        Returns:
            List of person dicts
        """
        result = self.dynamodb.list_people()
        if result["success"]:
            return result["people"]
        return []

    def update_person(self, person_id: str, updates: Dict) -> Dict:
        """
        Update person info in DynamoDB

        Args:
            person_id: Person ID
            updates: Dict with fields to update

        Returns:
            Update result dict
        """
        updates["updated_at"] = datetime.now().isoformat()
        result = self.dynamodb.update_person(person_id, updates)

        if result["success"]:
            logger.info(f"✅ Updated person in DynamoDB: {person_id}")
        else:
            logger.error(f"❌ Failed to update person: {result.get('error')}")

        return result


    def delete_person(self, person_id: str) -> Dict:
        """
        Delete person from DynamoDB

        Args:
            person_id: Person ID

        Returns:
            Delete result dict
        """
        result = self.dynamodb.delete_person(person_id)

        if result["success"]:
            logger.info(f"✅ Deleted person from DynamoDB: {person_id}")
        else:
            logger.error(f"❌ Failed to delete person: {result.get('error')}")

        return result

    def add_embedding(
        self, person_id: str, face_id: str, image_url: str, quality_score: float = 0.0
    ) -> Dict:
        """
        Add embedding record to DynamoDB

        Args:
            person_id: Person ID
            face_id: Rekognition Face ID
            image_url: S3 image URL
            quality_score: Face quality score

        Returns:
            Add result dict
        """
        import uuid

        embedding_id = f"emb_{uuid.uuid4().hex[:12]}"

        embedding_data = {
            "embedding_id": embedding_id,
            "person_id": person_id,
            "face_id": face_id,
            "image_url": image_url,
            "quality_score": quality_score,
            "created_at": datetime.now().isoformat(),
        }

        result = self.dynamodb.save_embedding(embedding_data)

        if result["success"]:


            logger.info(f"✅ Added embedding to DynamoDB: {embedding_id}")
        else:
            logger.error(f"❌ Failed to add embedding: {result.get('error')}")

        return result

    def get_embeddings(self, person_id: str) -> List[Dict]:
        """
        Get all embeddings for a person

        Args:
            person_id: Person ID

        Returns:
            List of embedding dicts
        """
        # dynamodb.get_embeddings_by_person() returns List[Dict] directly
        return self.dynamodb.get_embeddings_by_person(person_id)

    def search_people(self, query: str) -> List[Dict]:
        """
        Search people by name using DynamoDB's scan capabilities.

        Args:
            query: Search query for the user_name.

        Returns:
            List of matching person dicts.
        """
        result = self.dynamodb.search_people(query)
        if result["success"]:
            logger.info(f"✅ Found {len(result['people'])} people matching query: '{query}'")
            return result["people"]
        else:
            logger.error(f"❌ Failed to search people: {result.get('error')}")
            return []

    def check_health(self) -> Dict:
        """
        Check database connectivity and health.

        Returns:
            Dict with health status
        """
        # This will be implemented in the DynamoDBClient
        return self.dynamodb.check_health()
