"""
AWS Lambda Function: Face Identification (Standalone)
Simple version using only boto3 (no external dependencies)
"""

import json
import os
import base64
import boto3
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# Environment variables
REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
REKOGNITION_COLLECTION = os.environ.get("AWS_REKOGNITION_COLLECTION", "face-recognition-collection-dev")
S3_BUCKET = os.environ.get("AWS_S3_BUCKET")
PEOPLE_TABLE = os.environ.get("PERSON_TABLE", "face-recognition-people-dev")
MATCHES_TABLE = os.environ.get("MATCHES_TABLE", "face-recognition-matches-dev")

# Initialize AWS clients
rekognition = boto3.client('rekognition', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

# DynamoDB tables
people_table = dynamodb.Table(PEOPLE_TABLE) if PEOPLE_TABLE else None
matches_table = dynamodb.Table(MATCHES_TABLE) if MATCHES_TABLE else None


def lambda_handler(event, context):
    """
    Main Lambda handler for face identification
    
    Expected body:
    {
        "image_base64": "base64_encoded_image",
        "threshold": 80.0 (optional),
        "max_results": 5 (optional)
    }
    """
    logger.info("Face identification request received")
    
    try:
        # Parse request
        body = json.loads(event.get("body", "{}"))
        image_base64 = body.get("image_base64")
        
        if not image_base64:
            return create_response(400, {
                "success": False,
                "error": "Missing image_base64 in request body"
            })
        
        # Decode image
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            return create_response(400, {
                "success": False,
                "error": f"Invalid base64 image: {str(e)}"
            })
        
        # Configuration
        threshold = float(body.get("threshold", 80.0))
        max_results = int(body.get("max_results", 5))
        
        # Search faces in Rekognition collection
        logger.info(f"Searching faces in collection: {REKOGNITION_COLLECTION}")
        
        try:
            rekognition_response = rekognition.search_faces_by_image(
                CollectionId=REKOGNITION_COLLECTION,
                Image={'Bytes': image_bytes},
                MaxFaces=max_results,
                FaceMatchThreshold=threshold
            )
        except rekognition.exceptions.InvalidParameterException as e:
            return create_response(400, {
                "success": False,
                "error": f"No face detected in image: {str(e)}"
            })
        except Exception as e:
            logger.error(f"Rekognition search failed: {e}")
            return create_response(500, {
                "success": False,
                "error": f"Face search failed: {str(e)}"
            })
        
        # Process matches
        face_matches = rekognition_response.get('FaceMatches', [])
        
        if not face_matches:
            logger.info("No matching faces found")
            return create_response(200, {
                "success": True,
                "faces": [],
                "message": "No matching faces found",
                "count": 0
            })
        
        # Get person details from DynamoDB
        results = []
        for match in face_matches:
            face_id = match['Face']['FaceId']
            similarity = match['Similarity']
            external_image_id = match['Face'].get('ExternalImageId')
            
            person_data = {
                "face_id": face_id,
                "confidence": round(similarity, 2),
                "external_image_id": external_image_id
            }
            
            # Try to get person info from DynamoDB
            if people_table and external_image_id:
                try:
                    # External image ID is usually person_id
                    person_id = external_image_id.split('_')[0] if '_' in external_image_id else external_image_id
                    
                    db_response = people_table.get_item(Key={'person_id': person_id})
                    if 'Item' in db_response:
                        person_info = db_response['Item']
                        person_data.update({
                            "person_id": person_info.get("person_id"),
                            "name": person_info.get("name", "Unknown"),
                            "gender": person_info.get("gender"),
                            "birth_year": person_info.get("birth_year"),
                            "nationality": person_info.get("nationality"),
                            "created_at": person_info.get("created_at")
                        })
                except Exception as e:
                    logger.warning(f"Failed to get person info for {external_image_id}: {e}")
            
            results.append(person_data)
        
        # Log match to DynamoDB
        if matches_table:
            try:
                match_id = f"match_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
                matches_table.put_item(Item={
                    "match_id": match_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "person_id": results[0].get("person_id", "unknown") if results else "unknown",
                    "confidence": results[0]["confidence"] if results else 0,
                    "match_count": len(results)
                })
            except Exception as e:
                logger.warning(f"Failed to log match: {e}")
        
        logger.info(f"Found {len(results)} matching faces")
        
        return create_response(200, {
            "success": True,
            "faces": results,
            "count": len(results),
            "message": f"Found {len(results)} matching face(s)"
        })
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return create_response(500, {
            "success": False,
            "error": f"Internal server error: {str(e)}"
        })


def create_response(status_code, body):
    """Create API Gateway response with CORS headers"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps(body, default=str)
    }
