"""
Lambda Function: Enroll Orchestrator
Handles enrollment requests from API Gateway
"""

import json
import os
import base64
import uuid
import time
from datetime import datetime, timezone
import contextlib
import boto3
from typing import Any, Dict, List
from aws_xray_sdk.core import xray_recorder
# Helpers
def _annotate(**kwargs: Any) -> None:
    for key, value in kwargs.items():
        try:
            xray_recorder.put_annotation(key, value)
        except Exception:
            pass


def _subsegment(name: str):
    try:
        return xray_recorder.in_subsegment(name)
    except Exception:
        return contextlib.nullcontext()


# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Environment variables
RAW_IMAGES_BUCKET = os.environ["RAW_IMAGES_BUCKET"]
EMBEDDINGS_TABLE = os.environ["EMBEDDINGS_TABLE"]
ENVIRONMENT = os.environ["ENVIRONMENT"]
METRICS_ENABLED = os.environ.get("METRICS_CLOUDWATCH_ENABLED", "false").lower() == "true"
METRICS_NAMESPACE = os.environ.get("METRICS_NAMESPACE", "FaceRecognition/Realtime")
METRICS_SERVICE_NAME = os.environ.get("METRICS_SERVICE_NAME", "enroll-orchestrator")
cloudwatch = boto3.client("cloudwatch") if METRICS_ENABLED else None

# DynamoDB table
embeddings_table = dynamodb.Table(EMBEDDINGS_TABLE)


def _publish_metrics(result: str, duration_ms: float, extra_metrics: List[Dict[str, Any]] | None = None) -> None:
    if not METRICS_ENABLED or cloudwatch is None:
        return
    metric_data = [
        {
            "MetricName": "EnrollRequests",
            "Dimensions": [
                {"Name": "Environment", "Value": ENVIRONMENT},
                {"Name": "Service", "Value": METRICS_SERVICE_NAME},
                {"Name": "Result", "Value": result},
            ],
            "Unit": "Count",
            "Value": 1,
        },
        {
            "MetricName": "EnrollLatency",
            "Dimensions": [
                {"Name": "Environment", "Value": ENVIRONMENT},
                {"Name": "Service", "Value": METRICS_SERVICE_NAME},
                {"Name": "Result", "Value": result},
            ],
            "Unit": "Milliseconds",
            "Value": duration_ms,
        },
    ]
    if extra_metrics:
        for metric in extra_metrics:
            metric_data.append(
                {
                    "MetricName": metric["name"],
                    "Dimensions": [
                        {"Name": "Environment", "Value": ENVIRONMENT},
                        {"Name": "Service", "Value": METRICS_SERVICE_NAME},
                    ],
                    "Unit": metric.get("unit", "None"),
                    "Value": metric["value"],
                }
            )
    try:
        cloudwatch.put_metric_data(Namespace=METRICS_NAMESPACE, MetricData=metric_data)
    except Exception as metric_error:  # pylint: disable=broad-except
        print(f"CloudWatch metric publish failed: {metric_error}")


def is_admin(event: Dict[str, Any]) -> bool:
    """Checks if the user is in the 'admin' Cognito group."""
    try:
        # API Gateway with Cognito Authorizer passes claims in this structure
        groups = event["requestContext"]["authorizer"]["claims"].get("cognito:groups", [])
        # Ensure groups is a list before checking
        if groups and isinstance(groups, list):
            return "admin" in groups
        return False
    except (KeyError, TypeError):
        # This will happen if the authorizer is not configured or during test invocations
        print("Could not determine user groups from the event context.")
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for enrollment orchestration

    Expected input:
    {
        "body": {
            "user_id": "john_doe",
            "image_base64": "...",
            "metadata": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        }
    }
    """
    start_time = time.time()

    def _record(result: str, image_size_kb: float | None = None) -> None:
        duration_ms = (time.time() - start_time) * 1000
        extras = []
        if image_size_kb is not None:
            extras.append({"name": "EnrollImageSizeKB", "value": image_size_kb, "unit": "None"})
        _publish_metrics(result, duration_ms, extras)
        try:
            xray_recorder.put_metadata("duration_ms", duration_ms, "metrics")
            if image_size_kb is not None:
                xray_recorder.put_metadata("image_size_kb", image_size_kb, "metrics")
        except Exception:
            pass

    _annotate(function="enroll-orchestrator", environment=ENVIRONMENT)

    # Authorization Check: Only admins can enroll
    if not is_admin(event):
        _record("Forbidden")
        return response(403, {"error": "Permission denied. Administrator access required."})


    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("user_id")
        image_base64 = body.get("image_base64")
        metadata = body.get("metadata", {})
        if user_id:
            _annotate(user_id=user_id)

        # Validate input
        if not user_id or not image_base64:
            _record("BadRequest")
            return response(400, {"error": "Missing required fields: user_id, image_base64"})

        # Generate unique tracking ID
        tracking_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Decode image
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            _record("DecodeError")
            return response(400, {"error": f"Invalid base64 image: {str(e)}"})

        # Validate image size (max 5MB)
        if len(image_bytes) > 5 * 1024 * 1024:
            _record("PayloadTooLarge")
            return response(400, {"error": "Image size exceeds 5MB limit"})

        # Upload to S3 (will trigger image-processor Lambda)
        s3_key = f"raw/{user_id}/{tracking_id}.jpg"

        with _subsegment('s3_put_raw_image'):
        s3.put_object(
            Bucket=RAW_IMAGES_BUCKET,
            Key=s3_key,
            Body=image_bytes,
            ContentType="image/jpeg",
            Metadata={
                "user_id": user_id,
                "tracking_id": tracking_id,
                "timestamp": timestamp,
                "environment": ENVIRONMENT,
                **{k: str(v) for k, v in metadata.items()},
            },
        )

        print(f"Image uploaded to S3: s3://{RAW_IMAGES_BUCKET}/{s3_key}")

        # Create pending record in DynamoDB
        with _subsegment('dynamodb_put_enrollment'):
        embeddings_table.put_item(
            Item={
                "PK": f"USER#{user_id}",
                "SK": f"TRACKING#{tracking_id}",
                "tracking_id": tracking_id,
                "user_id": user_id,
                "status": "PENDING",
                "s3_key": s3_key,
                "created_at": timestamp,
                "metadata": metadata,
                "TTL": int(datetime.now(timezone.utc).timestamp()) + 86400,  # 24 hours
            }
        )

        _record("Accepted", image_size_kb=len(image_bytes) / 1024)
        return response(
            202,
            {
                "message": "Enrollment request accepted",
                "tracking_id": tracking_id,
                "user_id": user_id,
                "status": "PENDING",
                "timestamp": timestamp,
            },
        )

    except Exception as e:
        print(f"Error in enroll_orchestrator: {str(e)}")
        import traceback

        traceback.print_exc()

        _record("Error")
        return response(500, {"error": "Internal server error", "message": str(e)})


def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create HTTP response"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body),
    }
