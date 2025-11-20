"""DynamoDB Client wrapper for metadata storage."""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """DynamoDB client for managing face recognition metadata."""

    def __init__(
        self,
        region: str,
        people_table: str,
        embeddings_table: str,
        matches_table: str,
        enabled: bool = True,
    ):
        """Initialize DynamoDB client.

        Args:
            region: AWS region
            people_table: Name of the People table
            embeddings_table: Name of the Embeddings table
            matches_table: Name of the Matches table
            enabled: Enable AWS operations (False for local-only mode)
        """
        self.region = region
        self.enabled = enabled

        # Table names
        self.people_table = people_table
        self.embeddings_table = embeddings_table
        self.matches_table = matches_table

        self.dynamodb = None
        if self.enabled:
            try:
                self.dynamodb = boto3.resource("dynamodb", region_name=region)
                logger.info(f"✅ DynamoDB Client initialized: region={region}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize DynamoDB client: {e}")
                self.enabled = False

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert floats to Decimal for DynamoDB compatibility."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        return obj

    def save_person(self, person_data: Dict) -> Dict:
        """Save person metadata to DynamoDB People table.

        Args:
            person_data: Person data with keys:
                - person_id (required)
                - user_name (required)
                - gender, birth_year, hometown, residence (optional)
                - created_at, updated_at (optional)

        Returns:
            Dict with success status
        """
        result = {"success": False, "error": None}

        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        try:
            table = self.dynamodb.Table(self.people_table)

            # Convert floats to Decimal
            item = self._convert_floats_to_decimal(person_data)

            # Add timestamps if not present
            if "created_at" not in item:
                item["created_at"] = datetime.now(timezone.utc).isoformat()
            if "updated_at" not in item:
                item["updated_at"] = datetime.now(timezone.utc).isoformat()

            table.put_item(Item=item)

            logger.info(
                f"✅ Saved person to DynamoDB: {item.get('person_id')} - {item.get('user_name')}"
            )
            result["success"] = True

        except Exception as e:
            logger.error(f"❌ DynamoDB save_person failed: {e}")
            result["error"] = str(e)

        return result

    def update_person(self, person_id: str, updates: Dict) -> Dict:
        """Update person attributes in DynamoDB.

        Args:
            person_id: The ID of the person to update.
            updates: A dictionary of attributes to update.

        Returns:
            Dict with success status.
        """
        result = {"success": False, "error": None}

        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        try:
            table = self.dynamodb.Table(self.people_table)

            # Build the update expression
            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in updates.keys())
            expression_attribute_names = {f"#{k}": k for k in updates.keys()}
            expression_attribute_values = {f":{k}": v for k, v in updates.items()}

            table.update_item(
                Key={"person_id": person_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=self._convert_floats_to_decimal(
                    expression_attribute_values
                ),
            )

            logger.info(f"✅ Updated person in DynamoDB: {person_id}")
            result["success"] = True

        except Exception as e:
            logger.error(f"❌ DynamoDB update_person failed: {e}")
            result["error"] = str(e)

        return result

    def increment_embedding_count(self, person_id: str) -> Dict:
        """Atomically increment the embedding_count for a person.

        Args:
            person_id: The ID of the person to update.

        Returns:
            A dictionary with the result of the update operation.
        """
        result = {"success": False, "error": None}

        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        try:
            table = self.dynamodb.Table(self.people_table)
            table.update_item(
                Key={"person_id": person_id},
                UpdateExpression="SET embedding_count = if_not_exists(embedding_count, :start) + :inc",
                ExpressionAttributeValues={":inc": 1, ":start": 0},
            )
            result["success"] = True
        except Exception as e:
            logger.error(f"❌ DynamoDB increment_embedding_count failed: {e}")
            result["error"] = str(e)

        return result

    def get_person(self, person_id: str) -> Optional[Dict]:
        """Get person by ID from DynamoDB.

        Args:
            person_id: Person ID

        Returns:
            Person data dict or None
        """
        if not self.enabled:
            return None

        try:
            table = self.dynamodb.Table(self.people_table)
            response = table.get_item(Key={"person_id": person_id})

            if "Item" in response:
                return response["Item"]

        except Exception as e:
            logger.error(f"❌ DynamoDB get_person failed: {e}")

        return None

    def get_people_batch(self, person_ids: List[str]) -> Dict:
        """Get multiple people by a list of IDs using BatchGetItem.

        Args:
            person_ids: A list of person IDs.

        Returns:
            Dict with success status and a list of people.
        """
        result = {"success": False, "error": None, "people": []}

        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        if not person_ids:
            result["success"] = True
            return result

        try:
            keys = [{"person_id": pid} for pid in person_ids]
            response = self.dynamodb.batch_get_item(
                RequestItems={self.people_table: {"Keys": keys}}
            )

            people = response.get("Responses", {}).get(self.people_table, [])
            result["people"] = people
            result["success"] = True

            # Basic handling for unprocessed keys, can be made more robust
            unprocessed_keys = response.get("UnprocessedKeys", {}).get(self.people_table)
            if unprocessed_keys:
                logger.warning(f"Unprocessed keys in batch get: {len(unprocessed_keys['Keys'])}")

        except Exception as e:
            logger.error(f"❌ DynamoDB get_people_batch failed: {e}")
            result["error"] = str(e)

        return result

    def list_people(self, limit: int = 100) -> Dict:
        """List all people from DynamoDB.

        Args:
            limit: Maximum number of items to return

        Returns:
            Dict with success status and list of people
        """
        result = {"success": False, "error": None, "people": []}
        
        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        try:
            table = self.dynamodb.Table(self.people_table)
            response = table.scan(Limit=limit)

            result["success"] = True
            result["people"] = response.get("Items", [])
            return result

        except Exception as e:
            logger.error(f"❌ DynamoDB list_people failed: {e}")
            result["error"] = str(e)
            return result

    def search_people(self, query: str, limit: int = 100) -> Dict:
        """Search for people by name in DynamoDB.

        Args:
            query: The search string for the user_name.
            limit: Maximum number of items to return.

        Returns:
            Dict with success status and a list of people.
        """
        result = {"success": False, "error": None, "people": []}

        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        try:
            table = self.dynamodb.Table(self.people_table)

            # Case-insensitive search is not directly supported by contains.
            # A more advanced approach would involve a search service like OpenSearch/Elasticsearch.
            # For now, we perform a case-sensitive scan.
            response = table.scan(
                FilterExpression=Attr("user_name").contains(query),
                Limit=limit
            )

            people = response.get("Items", [])
            result["people"] = people
            result["success"] = True
            logger.info(f"✅ DynamoDB scan for '{query}' found {len(people)} items.")

        except Exception as e:
            logger.error(f"❌ DynamoDB search_people failed: {e}")
            result["error"] = str(e)

        return result

    def save_embedding(self, embedding_data: Dict) -> Dict:
        """Save face embedding to DynamoDB Embeddings table.

        Args:
            embedding_data: Embedding data with keys:
                - embedding_id (required)
                - person_id (required)
                - face_id (Rekognition face ID, optional)
                - image_url (S3 URL, optional)
                - quality_score, face_confidence (optional)
                - created_at (optional)

        Returns:
            Dict with success status
        """
        result = {"success": False, "error": None}

        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        try:
            table = self.dynamodb.Table(self.embeddings_table)

            # Convert floats to Decimal
            item = self._convert_floats_to_decimal(embedding_data)

            # Add timestamp if not present
            if "created_at" not in item:
                item["created_at"] = datetime.now(timezone.utc).isoformat()

            table.put_item(Item=item)

            logger.info(
                f"✅ Saved embedding to DynamoDB: {item.get('embedding_id')} for person {item.get('person_id')}"
            )
            result["success"] = True

        except Exception as e:
            logger.error(f"❌ DynamoDB save_embedding failed: {e}")
            result["error"] = str(e)

        return result

    def get_embeddings_by_person(self, person_id: str) -> List[Dict]:
        """Get all embeddings for a person.

        Args:
            person_id: Person ID

        Returns:
            List of embedding data dicts
        """
        if not self.enabled:
            return []

        try:
            table = self.dynamodb.Table(self.embeddings_table)

            # Query using GSI person_id-index
            response = table.query(
                IndexName="person_id-index",
                KeyConditionExpression="person_id = :pid",
                ExpressionAttributeValues={":pid": person_id},
            )

            return response.get("Items", [])

        except Exception as e:
            logger.error(f"❌ DynamoDB get_embeddings_by_person failed: {e}")
            return []

    def save_match(self, match_data: Dict) -> Dict:
        """Save identification match result to DynamoDB.

        Args:
            match_data: Match data with keys:
                - match_id (required)
                - person_id (required)
                - confidence (required)
                - image_url, location, device_id (optional)
                - timestamp (optional)

        Returns:
            Dict with success status
        """
        result = {"success": False, "error": None}

        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        try:
            table = self.dynamodb.Table(self.matches_table)

            # Convert floats to Decimal
            item = self._convert_floats_to_decimal(match_data)

            # Add timestamp if not present
            if "timestamp" not in item:
                item["timestamp"] = datetime.now(timezone.utc).isoformat()

            table.put_item(Item=item)

            logger.info(
                "✅ Saved match to DynamoDB: %s - person %s (confidence: %s)",
                item.get("match_id"),
                item.get("person_id"),
                item.get("confidence"),
            )
            result["success"] = True

        except Exception as e:
            logger.error(f"❌ DynamoDB save_match failed: {e}")
            result["error"] = str(e)

        return result

    def query_matches_by_person(self, person_id: str, limit: int = 100) -> List[Dict]:
        """Query matches for a specific person.

        Args:
            person_id: Person ID
            limit: Maximum number of results

        Returns:
            List of match data dicts
        """
        if not self.enabled:
            return []

        try:
            table = self.dynamodb.Table(self.matches_table)

            response = table.query(
                IndexName="person_id-index",
                KeyConditionExpression="person_id = :pid",
                ExpressionAttributeValues={":pid": person_id},
                Limit=limit,
                ScanIndexForward=False,  # Sort by timestamp descending
            )

            return response.get("Items", [])

        except Exception as e:
            logger.error(f"❌ DynamoDB query_matches_by_person failed: {e}")
            return []

    def delete_person(self, person_id: str) -> Dict:
        """Delete person from DynamoDB.

        Args:
            person_id: Person ID

        Returns:
            Dict with success status
        """
        result = {"success": False, "error": None}

        if not self.enabled:
            result["error"] = "DynamoDB not enabled"
            return result

        try:
            table = self.dynamodb.Table(self.people_table)
            table.delete_item(Key={"person_id": person_id})

            logger.info(f"✅ Deleted person from DynamoDB: {person_id}")
            result["success"] = True

        except Exception as e:
            logger.error(f"❌ DynamoDB delete_person failed: {e}")
            result["error"] = str(e)

        return result

    def check_health(self) -> Dict:
        """Check if DynamoDB tables are accessible."""
        if not self.enabled:
            return {"status": "disabled", "tables": []}

        try:
            # Check the status of the main 'people' table
            table = self.dynamodb.Table(self.people_table)
            table.load()  # This makes a describe_table call
            return {
                "status": "ok",
                "tables": [
                    self.people_table,
                    self.embeddings_table,
                    self.matches_table,
                ],
                "table_status": table.table_status,
            }
        except Exception as e:
            logger.error(f"❌ DynamoDB health check failed: {e}")
            return {"status": "error", "error": str(e)}
