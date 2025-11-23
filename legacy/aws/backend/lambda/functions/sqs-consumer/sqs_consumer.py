"""
Lambda Function: SQS Consumer
Processes realtime face recognition events from SQS queue
Triggered by SQS messages
"""

import json
import os
import base64
from datetime import datetime, timezone
import boto3
from typing import Dict, Any, List

# AWS clients
dynamodb = boto3.resource("dynamodb")
rekognition = boto3.client("rekognition")
eventbridge = boto3.client("events")

# Environment variables
EMBEDDINGS_TABLE = os.environ["EMBEDDINGS_TABLE"]
MATCH_HISTORY_TABLE = os.environ["MATCH_HISTORY_TABLE"]
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
ENVIRONMENT = os.environ["ENVIRONMENT"]

# DynamoDB tables
embeddings_table = dynamodb.Table(EMBEDDINGS_TABLE)
match_history_table = dynamodb.Table(MATCH_HISTORY_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process SQS messages batch

    Event structure:
    {
        "Records": [
            {
                "body": "json_string",
                "messageId": "...",
                "receiptHandle": "..."
            }
        ]
    }
    """
    processed = 0
    failed = 0

    try:
        for record in event.get("Records", []):
            try:
                # Parse SQS message
                message_body = json.loads(record["body"])

                print(
                    f"Processing SQS message: {message_body.get('device_id', 'unknown')}"
                )

                # Process face recognition event
                result = process_face_event(message_body)

                if result["success"]:
                    processed += 1

                    # Publish success event to EventBridge
                    publish_event(
                        {
                            "source": "face.recognition.sqs",
                            "detail-type": "FaceProcessed",
                            "detail": {
                                "device_id": message_body.get("device_id"),
                                "timestamp": result.get("timestamp"),
                                "quality_score": result.get("quality_score"),
                                "matches": result.get("matches", []),
                            },
                        }
                    )
                else:
                    failed += 1
                    print(f"Failed to process: {result.get('error')}")

            except Exception as e:
                failed += 1
                print(f"Error processing record: {str(e)}")
                import traceback

                traceback.print_exc()

        print(f"Batch complete: {processed} processed, {failed} failed")

        return {
            "statusCode": 200,
            "body": json.dumps({"processed": processed, "failed": failed}),
        }

    except Exception as e:
        print(f"Fatal error in sqs_consumer: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


def process_face_event(face_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process individual face recognition event"""
    try:
        device_id = face_data.get("device_id", "unknown")
        image_base64 = face_data.get("image_base64")
        location = face_data.get("location", "unknown")
        timestamp = face_data.get(
            "timestamp", datetime.now(timezone.utc).isoformat()
        )

        if not image_base64:
            return {"success": False, "error": "Missing image_base64"}

        # Decode image
        image_bytes = base64.b64decode(image_base64)

        # Use Rekognition to detect faces
        rekognition_response = rekognition.detect_faces(
            Image={"Bytes": image_bytes}, Attributes=["ALL"]
        )

        faces = rekognition_response.get("FaceDetails", [])

        if not faces:
            return {"success": False, "error": "No face detected"}

        face = faces[0]  # Take first face

        # Calculate quality score
        quality_score = calculate_quality_score(face)

        # Search for matches in enrolled faces
        matches = search_enrolled_faces(image_bytes)

        # Store in match history
        match_history_table.put_item(
            Item={
                "PK": f"DEVICE#{device_id}",
                "SK": f"EVENT#{timestamp}",
                "device_id": device_id,
                "location": location,
                "timestamp": timestamp,
                "quality_score": quality_score,
                "face_detected": True,
                "confidence": float(face.get("Confidence", 0)),
                "emotions": face.get("Emotions", []),
                "age_range": face.get("AgeRange", {}),
                "gender": face.get("Gender", {}),
                "matches": matches,
                "match_count": len(matches),
                "ttl": int(datetime.now(timezone.utc).timestamp() + 2592000),  # 30 days
            }
        )

        return {
            "success": True,
            "device_id": device_id,
            "quality_score": quality_score,
            "timestamp": timestamp,
            "matches": matches,
        }

    except Exception as e:
        print(f"Error in process_face_event: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


def search_enrolled_faces(image_bytes: bytes) -> List[Dict[str, Any]]:
    """Search for matching enrolled faces"""
    try:
        # Get all enrolled faces from DynamoDB
        response = embeddings_table.scan(
            ProjectionExpression="person_id, person_name, #img",
            ExpressionAttributeNames={"#img": "image_s3_key"},
        )

        matches = []

        for item in response.get("Items", []):
            person_id = item.get("person_id")
            person_name = item.get("person_name")

            # Skip if no data
            if not person_id or not person_name:
                continue

            matches.append(
                {
                    "person_id": person_id,
                    "person_name": person_name,
                    "confidence": 0.85,  # Placeholder - would use actual comparison
                }
            )

        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        return matches[:5]  # Top 5 matches

    except Exception as e:
        print(f"Error searching faces: {str(e)}")
        return []


def calculate_quality_score(face_details: Dict[str, Any]) -> float:
    """Calculate overall quality score from Rekognition face details"""
    try:
        quality = face_details.get("Quality", {})
        brightness = quality.get("Brightness", 50) / 100.0
        sharpness = quality.get("Sharpness", 50) / 100.0
        confidence = face_details.get("Confidence", 50) / 100.0

        # Weighted average
        score = brightness * 0.3 + sharpness * 0.3 + confidence * 0.4
        return round(score, 3)

    except Exception as e:
        print(f"Error calculating quality: {str(e)}")
        return 0.5


def publish_event(event_detail: Dict[str, Any]) -> None:
    """Publish event to EventBridge"""
    try:
        eventbridge.put_events(
            Entries=[
                {
                    "Source": event_detail["source"],
                    "DetailType": event_detail["detail-type"],
                    "Detail": json.dumps(event_detail["detail"]),
                    "EventBusName": EVENT_BUS_NAME,
                }
            ]
        )
        print(f"Published event: {event_detail['detail-type']}")
    except Exception as e:
        print(f"Error publishing event: {str(e)}")
