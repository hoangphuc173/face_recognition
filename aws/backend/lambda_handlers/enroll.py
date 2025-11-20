"""
Lambda Handler for Face Enrollment
- Triggered by API Gateway POST /enroll
- Expects a JSON body with 'image_base64' and user metadata.
"""

import base64
import json
import logging
import os

# Assuming boto3 is available in the Lambda environment
import boto3

# Import from backend package
from backend.core.enrollment_service import EnrollmentService
from backend.aws.s3_client import S3Client
from backend.aws.rekognition_client import RekognitionClient
from backend.aws.dynamodb_client import DynamoDBClient

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients outside the handler for reuse
# These environment variables would be set in the Lambda function configuration
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

enrollment_service = EnrollmentService(
    s3_client=s3_client,
    rekognition_client=rekognition_client,
    dynamodb_client=dynamodb_client,
)

def is_admin(event: dict) -> bool:
    """Checks if the user is in the 'admin' Cognito group from the JWT token."""
    try:
        # This path is for API Gateway HTTP APIs with a JWT authorizer.
        # For REST APIs, the path might be event["requestContext"]["authorizer"]["claims"]
        groups = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {}).get("cognito:groups", [])
        if isinstance(groups, str):
            groups = groups.split(' ')
        logger.info(f"User groups: {groups}")
        return "admin" in groups
    except (KeyError, TypeError):
        logger.warning("Could not find Cognito groups in the event token.")
        return False

def handler(event, context):
    """
    API Gateway Lambda Proxy integration handler.
    """
    try:
                logger.info(f"Received event: {json.dumps(event)}")

        # Authorization Check: Only admins can enroll new users
        if not is_admin(event):
            return {
                "statusCode": 403,
                "body": json.dumps({"message": "Permission denied. Admin access required."}),
            }

        # Parse the request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        image_base64 = body.get("image_base64")
        user_name = body.get("user_name")

        if not image_base64 or not user_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing required fields: image_base64, user_name"}),
            }

        # Decode the image
        image_bytes = base64.b64decode(image_base64)

        # Extract optional metadata
        gender = body.get("gender", "")
        birth_year = body.get("birth_year", "")
        hometown = body.get("hometown", "")
        residence = body.get("residence", "")

        # Call the enrollment service
        result = enrollment_service.enroll_face(
            image_bytes=image_bytes,
            user_name=user_name,
            gender=gender,
            birth_year=birth_year,
            hometown=hometown,
            residence=residence,
        )

        # Determine status code based on success
        status_code = 200 if result.get("success") else 500

        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",  # For development, be more specific in production
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

