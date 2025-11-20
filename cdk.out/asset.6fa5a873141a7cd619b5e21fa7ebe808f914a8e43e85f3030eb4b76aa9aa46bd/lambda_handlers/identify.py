"""
Lambda Handler for Face Identification
- Triggered by API Gateway POST /identify
- Expects a JSON body with 'image_base64'.
"""

import base64
import json
import logging
import os

import boto3

from backend.core.identification_service import IdentificationService
from backend.aws.s3_client import S3Client
from backend.aws.rekognition_client import RekognitionClient
from backend.aws.dynamodb_client import DynamoDBClient

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
REKOGNITION_COLLECTION_ID = os.environ.get("REKOGNITION_COLLECTION_ID")
DYNAMODB_PEOPLE_TABLE = os.environ.get("DYNAMODB_PEOPLE_TABLE")
DYNAMODB_EMBEDDINGS_TABLE = os.environ.get("DYNAMODB_EMBEDDINGS_TABLE")

# It's a best practice to initialize clients once
s3_client = S3Client(bucket_name=S3_BUCKET)
rekognition_client = RekognitionClient(collection_id=REKOGNITION_COLLECTION_ID)
dynamodb_client = DynamoDBClient(
    people_table=DYNAMODB_PEOPLE_TABLE, 
    embeddings_table=DYNAMODB_EMBEDDINGS_TABLE
)

identification_service = IdentificationService(
    rekognition_client=rekognition_client,
    dynamodb_client=dynamodb_client,
    s3_client=s3_client
)

def is_authenticated(event: dict) -> bool:
    """Checks if the request has a valid JWT token from Cognito by checking for claims."""
    try:
        # A valid token processed by a JWT authorizer will have a 'claims' object.
        claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
        # The 'sub' (subject) claim is a standard part of a JWT and indicates the user ID.
        return "sub" in claims
    except (KeyError, TypeError):
        logger.warning("Could not find Cognito authorizer claims in the event token.")
        return False

def handler(event, context):
    """
    API Gateway Lambda Proxy integration handler.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Authentication Check: Only authenticated users can identify faces
        if not is_authenticated(event):
            return {
                "statusCode": 401,
                "body": json.dumps({"message": "Unauthorized. Authentication required."}),
            }

        body = json.loads(event.get("body", "{}"))

        image_base64 = body.get("image_base64")
        if not image_base64:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing required field: image_base64"}),
            }

        image_bytes = base64.b64decode(image_base64)

        # Extract optional parameters
        confidence_threshold = float(body.get("confidence_threshold", 80.0))
        max_results = int(body.get("max_results", 5))

        # Call the identification service
        result = identification_service.identify_face(
            image_bytes=image_bytes,
            confidence_threshold=confidence_threshold,
            max_results=max_results,
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(result),
        }

    except base64.B64DecodeError:
        logger.error("Invalid base64 encoding.")
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid base64 image data"}),
        }
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body.")
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON format in request body"}),
        }
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Internal server error: {str(e)}"}),
        }

