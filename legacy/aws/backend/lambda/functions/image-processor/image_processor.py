"""
Lambda Function: Image Processor (Optimized with Rekognition Indexing)
Processes images from S3, indexes them directly into the Rekognition Collection.
Triggered by S3 PutObject event.
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# --- AWS Clients ---
try:
    s3_client = boto3.client("s3")
    rekognition_client = boto3.client("rekognition")
    dynamodb_resource = boto3.resource("dynamodb")
except Exception as e:
    logger.fatal(f"Failed to initialize AWS clients: {e}", exc_info=True)
    s3_client = rekognition_client = dynamodb_resource = None

# --- Environment Variables ---
REKOGNITION_COLLECTION_ID = os.environ.get("AWS_REKOGNITION_COLLECTION")
PERSON_TABLE_NAME = os.environ.get("PERSON_TABLE")

if not all([REKOGNITION_COLLECTION_ID, PERSON_TABLE_NAME]):
    raise EnvironmentError("Required env vars AWS_REKOGNITION_COLLECTION and PERSON_TABLE are not set.")

person_table = dynamodb_resource.Table(PERSON_TABLE_NAME) if dynamodb_resource else None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler triggered by S3 events to process and index faces.
    """
    if not all([s3_client, rekognition_client, person_table]):
        logger.error("A required AWS client is not initialized.")
        return {"statusCode": 500, "body": "Service initialization failed"}

    for record in event.get("Records", []):
        try:
            bucket_name = record["s3"]["bucket"]["name"]
            object_key = record["s3"]["object"]["key"]
            logger.info(f"Processing image: s3://{bucket_name}/{object_key}")

            # Get metadata from S3 object
            s3_object = s3_client.head_object(Bucket=bucket_name, Key=object_key)
            metadata = s3_object.get("Metadata", {})
            person_id = metadata.get("person_id")

            if not person_id:
                logger.error(f"Missing 'person_id' in S3 metadata for {object_key}")
                continue

            # 2. Index face directly into Rekognition Collection
            index_result = index_face_in_rekognition(bucket_name, object_key, person_id)

            if not index_result["success"]:
                logger.error(f"Failed to index face for {person_id}: {index_result.get('error')}")
                # Optionally, update a status table to reflect the failure
                continue

            # 3. Save person and face metadata to DynamoDB
            face_record = index_result["face_records"][0]
            save_person_metadata(person_id, face_record, metadata)

            logger.info(f"Successfully enrolled person '{person_id}' with FaceId '{face_record['face_id']}'")

        except Exception as e:
            logger.error(f"Error processing record: {record}", exc_info=True)
            # Continue to next record

    return {"statusCode": 200, "body": "Processing complete"}


def index_face_in_rekognition(bucket: str, key: str, person_id: str) -> Dict[str, Any]:
    """
    Calls Rekognition's IndexFaces API.
    This single call detects, extracts features, and stores the face embedding.
    """
    try:
        response = rekognition_client.index_faces(
            CollectionId=REKOGNITION_COLLECTION_ID,
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            ExternalImageId=person_id,  # Link this face to our internal person_id
            MaxFaces=1,
            QualityFilter="AUTO",
            DetectionAttributes=["DEFAULT"],
        )

        face_records = response.get("FaceRecords", [])
        if not face_records:
            return {"success": False, "error": "No face detected or quality too low."}

        logger.info(f"Rekognition indexed {len(face_records)} face(s).")
        return {"success": True, "face_records": face_records}

    except rekognition_client.exceptions.InvalidParameterException as e:
        logger.warning(f"Rekognition validation error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Rekognition index_faces failed: {e}", exc_info=True)
        return {"success": False, "error": f"Rekognition API error: {str(e)}"}

def save_person_metadata(person_id: str, face_record: Dict[str, Any], s3_metadata: Dict[str, Any]):
    """
    Saves or updates the person's record in DynamoDB with the new FaceId.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    face_id = face_record["Face"]["FaceId"]
    
    # Prepare item attributes, filtering out reserved keys from S3 metadata
    item = {
        'PersonId': person_id,
        'FaceId': face_id,
        'CreatedAt': timestamp,
        'LastUpdatedAt': timestamp,
        'Confidence': str(face_record["Face"]["Confidence"]),
        **{k: v for k, v in s3_metadata.items() if k not in ['person_id']} # Add other metadata
    }

    try:
        person_table.put_item(Item=item)
        logger.info(f"Saved metadata for PersonId '{person_id}' to DynamoDB.")
    except Exception as e:
        logger.error(f"DynamoDB put_item failed for PersonId '{person_id}': {e}", exc_info=True)
        # Depending on requirements, might need a retry or DLQ mechanism here
        raise
