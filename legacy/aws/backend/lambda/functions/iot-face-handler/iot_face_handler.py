"""
Lambda Function: IoT Face Handler
Handles face detection events from IoT devices
Triggered by IoT Rule Engine
"""

import json
import os
import base64
from datetime import datetime, timezone
import boto3
import numpy as np
from typing import Dict, Any, Optional

# AWS clients
iot_data = boto3.client("iot-data")
sagemaker_runtime = boto3.client("sagemaker-runtime")
rekognition = boto3.client("rekognition")
dynamodb = boto3.resource("dynamodb")

# Environment variables
EMBEDDINGS_TABLE = os.environ["EMBEDDINGS_TABLE"]
MATCH_HISTORY_TABLE = os.environ["MATCH_HISTORY_TABLE"]
SAGEMAKER_ENDPOINT = os.environ["SAGEMAKER_ENDPOINT"]

# DynamoDB tables
embeddings_table = dynamodb.Table(EMBEDDINGS_TABLE)
match_history_table = dynamodb.Table(MATCH_HISTORY_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Optional[Dict[str, Any]]:
    """
    Handle IoT face detection event

    IoT message structure:
    {
        "device_id": "camera_01",
        "image_base64": "...",
        "location": "entrance_lobby",
        "timestamp": "2025-11-14T10:30:00Z"
    }
    """
    try:
        device_id = event.get("device_id", "unknown")
        image_base64 = event.get("image_base64")
        location = event.get("location", "unknown")
        event_timestamp = event.get(
            "timestamp", datetime.now(timezone.utc).isoformat()
        )

        if not image_base64:
            publish_result(
                device_id, {"success": False, "error": "Missing image_base64"}
            )
            return

        # Decode image
        image_bytes = base64.b64decode(image_base64)

        # Fast path: Rekognition for quick detection
        rekognition_result = rekognition.detect_faces(
            Image={"Bytes": image_bytes}, Attributes=["DEFAULT"]
        )

        if not rekognition_result.get("FaceDetails"):
            publish_result(
                device_id,
                {
                    "success": True,
                    "matches": [],
                    "message": "No face detected",
                    "processing_time_ms": 0,
                },
            )
            return

        start_time = datetime.now(timezone.utc)

        # Precise path: SageMaker for accurate embedding
        query_embedding = generate_embedding_sagemaker(image_bytes)

        if not query_embedding:
            publish_result(
                device_id, {"success": False, "error": "Failed to generate embedding"}
            )
            return

        # Load and compare embeddings
        all_embeddings = load_all_embeddings()
        matches = find_matches(query_embedding, all_embeddings, top_k=3, threshold=0.7)

        # Calculate processing time
        processing_time = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

        # Prepare result
        result = {
            "success": True,
            "matches": matches,
            "device_id": device_id,
            "location": location,
            "processing_time_ms": int(processing_time),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Save to match history
        if matches:
            save_iot_match_history(device_id, location, matches[0], processing_time)

        # Publish result to IoT topic
        publish_result(device_id, result)

        # Update device shadow
        update_device_shadow(device_id, result)

        return result

    except Exception as e:
        print(f"Error in iot_face_handler: {str(e)}")
        import traceback

        traceback.print_exc()

        publish_result(
            event.get("device_id", "unknown"), {"success": False, "error": str(e)}
        )


def generate_embedding_sagemaker(image_bytes: bytes) -> Optional[np.ndarray]:
    """Generate embedding using SageMaker endpoint"""
    try:
        from PIL import Image
        from io import BytesIO

        # Preprocess
        image = Image.open(BytesIO(image_bytes))
        image = image.convert("RGB")
        image = image.resize((112, 112))
        image_array = np.array(image).astype(np.float32)
        image_array = (image_array - 127.5) / 128.0

        # Invoke SageMaker
        input_data = {"image": image_array.tolist(), "normalize": True}

        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType="application/json",
            Body=json.dumps(input_data),
        )

        result = json.loads(response["Body"].read())
        embedding = np.array(result["embeddings"], dtype=np.float32)
        embedding = embedding / np.linalg.norm(embedding)

        return embedding

    except Exception as e:
        print(f"SageMaker error: {str(e)}")
        return None


def load_all_embeddings():
    """Load all active embeddings"""
    embeddings = []

    try:
        response = embeddings_table.query(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :pk",
            ExpressionAttributeValues={":pk": "ACTIVE"},
        )

        for item in response.get("Items", []):
            embedding_binary = item.get("embedding_vector")
            if isinstance(embedding_binary, bytes):
                embedding_vector = np.frombuffer(embedding_binary, dtype=np.float32)
                embeddings.append(
                    {
                        "user_id": item.get("user_id"),
                        "embedding": embedding_vector,
                        "quality_score": float(item.get("quality_score", 0)),
                    }
                )

        return embeddings

    except Exception as e:
        print(f"Error loading embeddings: {str(e)}")
        return []


def find_matches(
    query_embedding: np.ndarray, all_embeddings, top_k: int, threshold: float
):
    """Find matching faces"""
    similarities = []

    for item in all_embeddings:
        similarity = np.dot(query_embedding, item["embedding"])

        if similarity >= threshold:
            similarities.append(
                {
                    "user_id": item["user_id"],
                    "confidence": float(similarity),
                    "quality_score": item["quality_score"],
                }
            )

    similarities.sort(key=lambda x: x["confidence"], reverse=True)
    return similarities[:top_k]


def save_iot_match_history(
    device_id: str, location: str, match: Dict[str, Any], processing_time: float
):
    """Save IoT match to history"""
    try:
        timestamp = datetime.now(timezone.utc).isoformat()

        match_history_table.put_item(
            Item={
                "PK": f"DEVICE#{device_id}",
                "SK": timestamp,
                "device_id": device_id,
                "location": location,
                "matched_user_id": match["user_id"],
                "confidence": str(match["confidence"]),
                "processing_time_ms": int(processing_time),
                "timestamp": timestamp,
                "ttl": int(datetime.now(timezone.utc).timestamp()) + 30 * 86400,
            }
        )
    except Exception as e:
        print(f"Error saving history: {str(e)}")


def publish_result(device_id: str, result: Dict[str, Any]):
    """Publish result to IoT topic"""
    try:
        topic = f"devices/{device_id}/face/result"

        iot_data.publish(topic=topic, qos=1, payload=json.dumps(result))

        print(f"Published to {topic}: {result}")

    except Exception as e:
        print(f"IoT publish error: {str(e)}")


def update_device_shadow(device_id: str, result: Dict[str, Any]):
    """Update device shadow with latest detection"""
    try:
        shadow_update = {
            "state": {
                "reported": {
                    "last_detection": result["timestamp"],
                    "last_match": (
                        result["matches"][0] if result.get("matches") else None
                    ),
                    "processing_time_ms": result.get("processing_time_ms", 0),
                }
            }
        }

        iot_data.update_thing_shadow(
            thingName=device_id, payload=json.dumps(shadow_update)
        )

    except Exception as e:
        print(f"Shadow update error: {str(e)}")
