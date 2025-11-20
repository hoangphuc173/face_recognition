"""
AWS Service Clients
- S3Client: For S3 operations (e.g., uploading images)
- RekognitionClient: For face recognition operations
- DynamoDBClient: For database operations

This module centralizes all boto3 interactions.
"""

import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Client:
    """Client for interacting with AWS S3."""

    def __init__(self, bucket_name: str, region_name: str = 'us-east-1'):
        if not bucket_name:
            raise ValueError("S3 bucket name is required.")
        self.s3 = boto3.client('s3', region_name=region_name)
        self.bucket_name = bucket_name
        self.region_name = region_name
        logger.info(f"S3Client initialized for bucket: {self.bucket_name}")

    def upload_bytes(self, data: bytes, key: str) -> dict:
        """Uploads bytes data to S3."""
        try:
            self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=data)
            url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"
            logger.info(f"Successfully uploaded to s3://{self.bucket_name}/{key}")
            return {"success": True, "url": url, "key": key}
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return {"success": False, "error": str(e)}


class RekognitionClient:
    """Client for interacting with AWS Rekognition."""

    def __init__(self, collection_id: str, region_name: str = 'us-east-1'):
        if not collection_id:
            raise ValueError("Rekognition collection ID is required.")
        self.rekognition = boto3.client('rekognition', region_name=region_name)
        self.collection_id = collection_id
        logger.info(f"RekognitionClient initialized for collection: {self.collection_id}")

    def index_face(self, image_bytes: bytes, external_image_id: str, max_faces: int = 1) -> dict:
        """Indexes a face into the collection."""
        try:
            response = self.rekognition.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_image_id,
                MaxFaces=max_faces,
                QualityFilter="AUTO",
                DetectionAttributes=['DEFAULT']
            )
            if response['FaceRecords']:
                face = response['FaceRecords'][0]
                return {
                    "success": True,
                    "face_id": face['Face']['FaceId'],
                    "quality_score": face['FaceDetail']['Quality']['Sharpness']
                }
            return {"success": False, "error": "No faces detected"}
        except ClientError as e:
            logger.error(f"Rekognition index_faces failed: {e}")
            return {"success": False, "error": str(e)}

    def search_faces(self, image_bytes: bytes, max_faces: int, face_match_threshold: float) -> dict:
        """Searches for matching faces in the collection."""
        try:
            response = self.rekognition.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=max_faces,
                FaceMatchThreshold=face_match_threshold
            )
            matches = [
                {
                    "face_id": match['Face']['FaceId'],
                    "external_image_id": match['Face']['ExternalImageId'],
                    "similarity": match['Similarity']
                }
                for match in response['FaceMatches']
            ]
            return {"success": True, "matches": matches}
        except ClientError as e:
            logger.error(f"Rekognition search_faces_by_image failed: {e}")
            return {"success": False, "error": str(e)}


class DynamoDBClient:
    """Client for interacting with AWS DynamoDB."""

    def __init__(self, people_table: str, embeddings_table: str, region_name: str = 'us-east-1'):
        if not people_table or not embeddings_table:
            raise ValueError("DynamoDB table names are required.")
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.people_table = self.dynamodb.Table(people_table)
        self.embeddings_table = self.dynamodb.Table(embeddings_table)
        logger.info(f"DynamoDBClient initialized for tables: {people_table}, {embeddings_table}")

    def save_person(self, person_data: dict) -> dict:
        """Saves a person's data to the people table."""
        try:
            self.people_table.put_item(Item=person_data)
            return {"success": True}
        except ClientError as e:
            logger.error(f"DynamoDB save_person failed: {e}")
            return {"success": False, "error": str(e)}

    def get_person(self, person_id: str) -> dict:
        """Retrieves a person's data from the people table."""
        try:
            response = self.people_table.get_item(Key={'person_id': person_id})
            if 'Item' in response:
                return {"success": True, "person": response['Item']}
            return {"success": False, "error": "Person not found"}
        except ClientError as e:
            logger.error(f"DynamoDB get_person failed: {e}")
            return {"success": False, "error": str(e)}

    def update_person(self, person_id: str, updates: dict) -> dict:
        """Updates a person's data in the people table."""
        try:
            expression_attribute_names = {}
            expression_attribute_values = {}
            update_expression = "SET "
            for key, value in updates.items():
                update_expression += f" #{key} = :{key},"
                expression_attribute_names[f"#{key}"] = key
                expression_attribute_values[f":{key}"] = value
            
            self.people_table.update_item(
                Key={'person_id': person_id},
                UpdateExpression=update_expression.rstrip(','),
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            return {"success": True}
        except ClientError as e:
            logger.error(f"DynamoDB update_person failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_person(self, person_id: str) -> dict:
        """Deletes a person from the people table."""
        try:
            self.people_table.delete_item(Key={'person_id': person_id})
            return {"success": True}
        except ClientError as e:
            logger.error(f"DynamoDB delete_person failed: {e}")
            return {"success": False, "error": str(e)}

    def search_people_by_name(self, name_query: str) -> dict:
        """Scans the people table for user_name containing the query string."""
        try:
            # Note: A scan on a large table can be slow and costly. 
            # For production scale, a search service like OpenSearch is recommended.
            # This is case-sensitive. For case-insensitive, you'd need to store a lowercase version.
            response = self.people_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('user_name').contains(name_query)
            )
            return {"success": True, "people": response.get('Items', [])}
        except ClientError as e:
            logger.error(f"DynamoDB scan by name failed: {e}")
            return {"success": False, "error": str(e), "people": []}

    def list_people(self) -> dict:
        """Lists all people from the people table."""
        try:
            response = self.people_table.scan()
            return {"success": True, "people": response.get('Items', [])}
        except ClientError as e:
            logger.error(f"DynamoDB list_people failed: {e}")
            return {"success": False, "error": str(e), "people": []}

    def save_embedding(self, embedding_data: dict) -> dict:
        """Saves an embedding's data to the embeddings table."""
        try:
            self.embeddings_table.put_item(Item=embedding_data)
            return {"success": True}
        except ClientError as e:
            logger.error(f"DynamoDB save_embedding failed: {e}")
            return {"success": False, "error": str(e)}

    def check_health(self) -> dict:
        """Checks connectivity to the DynamoDB tables."""
        try:
            self.dynamodb.meta.client.describe_table(TableName=self.people_table.name)
            self.dynamodb.meta.client.describe_table(TableName=self.embeddings_table.name)
            return {"status": "ok", "message": "DynamoDB connection successful."}
        except ClientError as e:
            logger.error(f"DynamoDB health check failed: {e}")
            return {"status": "error", "message": str(e)}

