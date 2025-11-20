"""
Lambda Function: People Manager
Handles CRUD operations for people records in DynamoDB and Rekognition.
Triggered by API Gateway
"""

import json
import os
import logging
from typing import Any, Dict, List

import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# --- AWS Clients ---
try:
    dynamodb_resource = boto3.resource("dynamodb")
    rekognition_client = boto3.client("rekognition")
except Exception as e:
    logger.fatal(f"Failed to initialize AWS clients: {e}", exc_info=True)
    dynamodb_resource = rekognition_client = None

# --- Environment Variables ---
PERSON_TABLE_NAME = os.environ.get("PERSON_TABLE")
REKOGNITION_COLLECTION_ID = os.environ.get("AWS_REKOGNITION_COLLECTION")

if not all([PERSON_TABLE_NAME, REKOGNITION_COLLECTION_ID]):
    raise EnvironmentError("Required env vars PERSON_TABLE and AWS_REKOGNITION_COLLECTION are not set.")

person_table = dynamodb_resource.Table(PERSON_TABLE_NAME) if dynamodb_resource else None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler to route CRUD operations for people.
    """
    if not person_table or not rekognition_client:
        return response(500, {"error": "Service initialization failed"})

    http_method = event.get("httpMethod", "").upper()
    path = event.get("path", "")
    person_id = event.get("pathParameters", {}).get("person_id")

    logger.info(f"Request: {http_method} {path}")

    try:
        if http_method == "GET":
            if person_id:
                return get_person(person_id)
            else:
                return get_all_people()
        elif http_method == "PUT" and person_id:
            body = json.loads(event.get("body", "{}"))
            return update_person(person_id, body)
        elif http_method == "DELETE" and person_id:
            return delete_person(person_id)
        else:
            return response(400, {"error": "Unsupported method or path"})

    except Exception as e:
        logger.error(f"Unhandled error for {http_method} {path}: {e}", exc_info=True)
        return response(500, {"error": "Internal Server Error", "message": str(e)})

def get_all_people() -> Dict[str, Any]:
    """Scans the DynamoDB table to get all person records."""
    try:
        scan_response = person_table.scan()
        items = scan_response.get("Items", [])
        # Handle pagination if necessary
        while 'LastEvaluatedKey' in scan_response:
            scan_response = person_table.scan(ExclusiveStartKey=scan_response['LastEvaluatedKey'])
            items.extend(scan_response.get("Items", []))
        logger.info(f"Found {len(items)} people in the table.")
        return response(200, items)
    except Exception as e:
        logger.error(f"Failed to scan person table: {e}", exc_info=True)
        raise

def get_person(person_id: str) -> Dict[str, Any]:
    """Gets a single person record by PersonId."""
    try:
        get_response = person_table.get_item(Key={'PersonId': person_id})
        if 'Item' not in get_response:
            return response(404, {"error": f"Person with ID '{person_id}' not found"})
        return response(200, get_response['Item'])
    except Exception as e:
        logger.error(f"Failed to get person '{person_id}': {e}", exc_info=True)
        raise

def update_person(person_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Updates a person's metadata."""
    try:
        # Construct UpdateExpression and ExpressionAttributeValues from the input data
        update_expression = "SET "
        expression_values = {}
        for key, value in data.items():
            if key != 'PersonId': # Don't allow changing the partition key
                update_expression += f"#{key} = :{key}, "
                expression_values[f":{key}"] = value
        
        if not expression_values:
            return response(400, {"error": "No update data provided"})

        update_expression = update_expression.rstrip(', ')
        expression_names = {f"#{key}": key for key in data if key != 'PersonId'}

        updated_item = person_table.update_item(
            Key={'PersonId': person_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        logger.info(f"Successfully updated person '{person_id}'.")
        return response(200, updated_item.get('Attributes', {}))
    except Exception as e:
        logger.error(f"Failed to update person '{person_id}': {e}", exc_info=True)
        raise

def delete_person(person_id: str) -> Dict[str, Any]:
    """Deletes a person from DynamoDB and their face from Rekognition."""
    try:
        # 1. Get the FaceId from DynamoDB before deleting the item
        get_response = person_table.get_item(Key={'PersonId': person_id})
        if 'Item' not in get_response:
            return response(404, {"error": f"Person with ID '{person_id}' not found"})
        
        face_id = get_response['Item'].get('FaceId')

        # 2. Delete face from Rekognition Collection
        if face_id:
            try:
                rekognition_client.delete_faces(
                    CollectionId=REKOGNITION_COLLECTION_ID,
                    FaceIds=[face_id]
                )
                logger.info(f"Deleted FaceId '{face_id}' from Rekognition for person '{person_id}'.")
            except Exception as e:
                # Log the error but proceed to delete from DynamoDB anyway
                logger.error(f"Failed to delete face '{face_id}' from Rekognition: {e}", exc_info=True)

        # 3. Delete item from DynamoDB
        person_table.delete_item(Key={'PersonId': person_id})
        logger.info(f"Deleted person '{person_id}' from DynamoDB.")

        return response(204, {})
    except Exception as e:
        logger.error(f"Failed to delete person '{person_id}': {e}", exc_info=True)
        raise

def response(status_code: int, body: Any) -> Dict[str, Any]:
    """Creates a standard API Gateway proxy response."""
    if status_code == 204: # No Content
        return {"statusCode": 204}

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body, default=str)
    }

