"""
Lambda Function: Telemetry Handler
Receives client telemetry payloads and stores them in DynamoDB.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from decimal import Decimal

import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TELEMETRY_TABLE"])

ALLOWED_FIELDS = {
    "client_id",
    "transport",
    "latency_ms",
    "status",
    "error_message",
    "frames_per_minute",
    "dropped_frames",
    "device",
    "faces_detected",
    "api_endpoint",
    "interval_seconds",
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Store telemetry payload."""
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON"})

    if not isinstance(body, dict):
        return _response(400, {"error": "Body must be an object"})

    client_id = str(body.get("client_id") or f"anon-{context.aws_request_id}")
    status = str(body.get("status") or "unknown")
    transport = str(body.get("transport") or "rest")
    timestamp = body.get("timestamp") or datetime.now(timezone.utc).isoformat()
    faces_detected = body.get("faces_detected", 0)

    item = {
        "PK": f"CLIENT#{client_id}",
        "SK": f"TS#{timestamp}",
        "client_id": client_id,
        "status": status,
        "transport": transport,
        "faces_detected": faces_detected,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "telemetry_id": str(uuid.uuid4()),
        "TTL": int(datetime.now(timezone.utc).timestamp()) + 30 * 24 * 3600,
    }

    for key in ALLOWED_FIELDS:
        if key in body and body[key] is not None:
            item[key] = body[key]

    try:
        table.put_item(Item=_convert(item))
    except Exception as exc:  # pylint: disable=broad-except
        return _response(
            500, {"error": "Failed to store telemetry", "details": str(exc)}
        )

    return _response(
        202, {"message": "Telemetry accepted", "telemetry_id": item["telemetry_id"]}
    )


def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def _convert(obj: Any) -> Any:
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert(v) for v in obj]
    return obj
