"""
WebSocket handler for realtime face recognition.

Routes handled:
    - $connect / $disconnect for API key validation
    - identify (default) to relay frames to IdentifyHandler Lambda
"""

from __future__ import annotations

import base64
import json
import logging
import os
import contextlib
from typing import Any, Dict, Optional

import boto3
from aws_xray_sdk.core import xray_recorder
from jwt import InvalidTokenError, PyJWKClient, decode as jwt_decode

LOGGER = logging.getLogger()
LOGGER.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

lambda_client = boto3.client("lambda")

IDENTIFY_LAMBDA_ARN = os.environ.get("IDENTIFY_LAMBDA_ARN", "")
API_KEY_VALUE = os.environ.get("API_KEY_VALUE", "")
API_KEY_HEADER = os.environ.get("API_KEY_HEADER", "x-api-key").lower()
DEFAULT_THRESHOLD = float(os.environ.get("DEFAULT_THRESHOLD", "0.6"))
COGNITO_ENABLED = os.environ.get("COGNITO_ENABLED", "false").lower() == "true"
COGNITO_REGION = os.environ.get("COGNITO_REGION", "")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "")
_ISSUER = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
    if COGNITO_ENABLED and COGNITO_USER_POOL_ID
    else ""
)
_JWK_CLIENT = PyJWKClient(f"{_ISSUER}/.well-known/jwks.json") if _ISSUER else None


def _xray_available() -> bool:
    try:
        return xray_recorder.current_segment() is not None
    except Exception:
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Entry point for API Gateway WebSocket events."""
    LOGGER.debug("WS Event: %s", json.dumps(event))
    event_type = event.get("requestContext", {}).get("eventType")
    try:
        xray_recorder.put_annotation("function", "websocket-handler")
        xray_recorder.put_annotation("event_type", event_type or "UNKNOWN")
    except Exception:
        pass

    if event_type == "CONNECT":
        if not _authenticate_event(event):
            LOGGER.warning("Unauthorized WebSocket connection attempt")
            return {"statusCode": 401, "body": "Unauthorized"}
        return {"statusCode": 200, "body": "Connected"}

    if event_type == "DISCONNECT":
        LOGGER.debug(
            "Connection %s disconnected", event["requestContext"]["connectionId"]
        )
        return {"statusCode": 200, "body": "Disconnected"}

    # Default/data route
    try:
        body = _parse_body(event.get("body"))
        action = body.get("action", "identify")
        if action != "identify":
            return _send_message(event, {"error": f"Unknown action '{action}'"})
        if not _authorize_message(event, body):
            return _send_message(event, {"error": "Unauthorized"}, status=401)

        image_base64 = body.get("image_base64")
        if not image_base64:
            return _send_message(event, {"error": "image_base64 is required"})

        # Basic payload size guard (~2.5MB)
        if len(image_base64) > 3_500_000:
            return _send_message(event, {"error": "Payload too large"})

        # Validate base64 upfront
        try:
            base64.b64decode(image_base64, validate=True)
        except Exception:
            return _send_message(event, {"error": "Invalid base64 payload"})

        identify_payload = {
            "body": json.dumps(
                {
                    "image_base64": image_base64,
                    "top_k": body.get("top_k", 5),
                    "threshold": body.get("threshold", DEFAULT_THRESHOLD),
                    "device_id": body.get(
                        "device_id",
                        event["requestContext"].get("connectionId", "unknown"),
                    ),
                }
            )
        }

        if not IDENTIFY_LAMBDA_ARN:
            raise RuntimeError("IDENTIFY_LAMBDA_ARN not configured")

        with (
            xray_recorder.in_subsegment("invoke_identify_lambda")
            if _xray_available()
            else contextlib.nullcontext()
        ):
            response = lambda_client.invoke(
                FunctionName=IDENTIFY_LAMBDA_ARN,
                InvocationType="RequestResponse",
                Payload=json.dumps(identify_payload).encode("utf-8"),
            )

        payload_bytes = response["Payload"].read()
        payload_text = (
            payload_bytes.decode("utf-8")
            if isinstance(payload_bytes, bytes)
            else str(payload_bytes)
        )
        LOGGER.debug("Identify Lambda response: %s", payload_text)
        try:
            lambda_result = json.loads(payload_text)
        except json.JSONDecodeError:
            lambda_result = {"statusCode": 500, "body": payload_text}

        message = _coerce_message(lambda_result)
        return _send_message(event, message)

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("WebSocket processing error: %s", exc)
        return _send_message(
            event, {"error": "Internal server error", "message": str(exc)}, status=500
        )


def _authenticate_event(event: Dict[str, Any]) -> bool:
    token = _extract_token(event)
    if token and _verify_jwt(token):
        return True
    if API_KEY_VALUE:
        headers = event.get("headers") or {}
        header_value = None
        for key, value in headers.items():
            if key.lower() == API_KEY_HEADER:
                header_value = value
                break
        if header_value == API_KEY_VALUE:
            return True
        query_params = event.get("queryStringParameters") or {}
        query_key = query_params.get("api_key") if query_params else None
        if query_key == API_KEY_VALUE:
            return True
    if COGNITO_ENABLED:
        return False
    return not API_KEY_VALUE


def _extract_token(event: Dict[str, Any]) -> Optional[str]:
    headers = event.get("headers") or {}
    for key, value in headers.items():
        if key.lower() == "authorization":
            parts = value.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
    query_params = event.get("queryStringParameters") or {}
    if query_params:
        return query_params.get("token")
    return None


def _authorize_message(event: Dict[str, Any], body: Dict[str, Any]) -> bool:
    token = body.get("token") or _extract_token(event)
    if token and _verify_jwt(token):
        return True
    return _authenticate_event(event)


def _verify_jwt(token: str) -> bool:
    if not COGNITO_ENABLED or not _JWK_CLIENT:
        return False
    try:
        signing_key = _JWK_CLIENT.get_signing_key_from_jwt(token)
        jwt_decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=_ISSUER,
        )
        return True
    except InvalidTokenError as err:
        LOGGER.warning("Invalid JWT: %s", err)
        return False


def _management_client(event: Dict[str, Any]):
    domain = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]
    endpoint_url = f"https://{domain}/{stage}"
    return boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)


def _send_message(
    event: Dict[str, Any], message: Dict[str, Any], status: int = 200
) -> Dict[str, Any]:
    """Send message back to the WebSocket client."""
    try:
        mgmt = _management_client(event)
        mgmt.post_to_connection(
            ConnectionId=event["requestContext"]["connectionId"],
            Data=json.dumps(message).encode("utf-8"),
        )
    except Exception as err:  # pylint: disable=broad-except
        LOGGER.error("Failed to post to connection: %s", err)

    return {"statusCode": status}


def _parse_body(body: Optional[str]) -> Dict[str, Any]:
    if not body:
        return {}
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


def _coerce_message(lambda_result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize payload from Identify Lambda."""
    body = lambda_result.get("body")
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body, "statusCode": lambda_result.get("statusCode", 200)}
    if isinstance(body, dict):
        return body
    return lambda_result
