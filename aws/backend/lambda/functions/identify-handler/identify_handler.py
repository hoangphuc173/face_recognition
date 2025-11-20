"""
Lambda Function: Identify Handler (Optimized with Rekognition Collection and DynamoDB Cache)
Identifies faces using Rekognition Search and implements a caching layer to reduce costs.
Triggered by API Gateway
"""

import json
import os
import base64
import time
import logging
import hashlib
from typing import Any, Dict
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# Import core services from the backend layer
from core.identification_service import IdentificationService
from aws.rekognition_client import RekognitionClient
from aws.dynamodb_client import DynamoDBClient

# --- Service Initialization ---

# Environment variables
REKOGNITION_COLLECTION_ID = os.environ.get("AWS_REKOGNITION_COLLECTION")
PERSON_TABLE_NAME = os.environ.get("PERSON_TABLE")
CACHE_TABLE_NAME = os.environ.get("CACHE_TABLE")
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
CACHE_TTL_MINUTES = int(os.environ.get("CACHE_TTL_MINUTES", "60"))

if not all([REKOGNITION_COLLECTION_ID, PERSON_TABLE_NAME, CACHE_TABLE_NAME]):
    raise EnvironmentError("Required env vars AWS_REKOGNITION_COLLECTION, PERSON_TABLE, and CACHE_TABLE are not set.")

# Initialize services
try:
    import boto3
    rekognition_client = RekognitionClient(collection_id=REKOGNITION_COLLECTION_ID, region=AWS_REGION)
    dynamodb_client = DynamoDBClient(table_name=PERSON_TABLE_NAME, region=AWS_REGION)
    identification_service = IdentificationService(rekognition_client=rekognition_client, dynamodb_client=dynamodb_client)
    
    # Client for the cache table
    dynamodb_resource = boto3.resource('dynamodb', region_name=AWS_REGION)
    cache_table = dynamodb_resource.Table(CACHE_TABLE_NAME)
    
    logger.info("Services initialized successfully.")
except Exception as e:
    logger.fatal(f"Failed to initialize services: {e}", exc_info=True)
    identification_service = None
    cache_table = None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for face identification with caching.
    """
    start_time = time.time()

    if not identification_service or not cache_table:
        return response(500, {"error": "ServiceInitializationError", "message": "Core services failed to initialize."})

    try:
        # 1. Parse request
        body = json.loads(event.get("body", "{}"))
        image_base64 = body.get("image_base64")
        if not image_base64:
            return response(400, {"error": "Missing image_base64"})

        # 2. Decode image and calculate hash for caching
        try:
            image_bytes = base64.b64decode(image_base64)
            image_hash = hashlib.sha256(image_bytes).hexdigest()
        except Exception as e:
            return response(400, {"error": f"Invalid base64: {str(e)}"})

        # 3. Check cache first
        try:
            cached_item = cache_table.get_item(Key={'ImageHash': image_hash})
            if 'Item' in cached_item:
                logger.info(f"Cache hit for hash: {image_hash}")
                cached_result = json.loads(cached_item['Item']['ResultData'])
                # Add a header to indicate cache hit for debugging
                return response(200, cached_result, {"X-Cache-Status": "Hit"})
        except Exception as e:
            logger.error(f"Cache read failed: {e}", exc_info=True)
            # Continue without cache if read fails

        logger.info(f"Cache miss for hash: {image_hash}. Proceeding with identification.")

        # 4. If cache miss, call Identification Service
        max_results = int(body.get("top_k", 5))
        threshold = float(body.get("threshold", 80.0))
        
        result = identification_service.identify_face(
            image_bytes=image_bytes,
            max_results=max_results,
            confidence_threshold=threshold,
            save_result=False
        )

        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Identification completed in {duration_ms:.2f} ms.")

        if not result["success"]:
            return response(500, {"error": "IdentificationFailed", "message": result.get("message")})

        # 5. Store successful result in cache
        if result.get("faces"):
            try:
                ttl = int(time.time()) + (CACHE_TTL_MINUTES * 60)
                cache_table.put_item(
                    Item={
                        'ImageHash': image_hash,
                        'ResultData': json.dumps(result, default=str),
                        'ttl': ttl
                    }
                )
                logger.info(f"Result stored in cache with TTL of {CACHE_TTL_MINUTES} minutes.")
            except Exception as e:
                logger.error(f"Cache write failed: {e}", exc_info=True)

        # 6. Return response
        return response(200, result, {"X-Cache-Status": "Miss"})

    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return response(500, {"error": "InternalServerError", "message": str(e)})


def response(status_code: int, body: Dict[str, Any], headers: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Creates a standard API Gateway proxy response.
    """
    base_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
    }
    if headers:
        base_headers.update(headers)
        
    return {
        "statusCode": status_code,
        "headers": base_headers,
        "body": json.dumps(body, default=str)
    }
