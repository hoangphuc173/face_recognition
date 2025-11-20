"""
Lambda Function: Realtime Notifier
Sends real-time notifications via WebSocket API
Triggered by DynamoDB Streams
"""

import json
import os
from datetime import datetime, timezone
import boto3
from typing import Dict, Any, List

# AWS clients
apigateway_management = None  # Initialized dynamically
sns = boto3.client("sns")

# Environment variables
WEBSOCKET_ENDPOINT = os.environ.get("WEBSOCKET_ENDPOINT", "")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process DynamoDB Stream events and send WebSocket notifications

    DynamoDB Stream event structure:
    {
        "Records": [{
            "eventName": "INSERT | MODIFY | REMOVE",
            "dynamodb": {
                "NewImage": {...},
                "OldImage": {...}
            }
        }]
    }
    """
    try:
        for record in event.get("Records", []):
            event_name = record.get("eventName")

            if event_name == "INSERT":
                handle_insert(record)
            elif event_name == "MODIFY":
                handle_modify(record)
            elif event_name == "REMOVE":
                handle_remove(record)

        return {"statusCode": 200, "body": "Notifications sent"}

    except Exception as e:
        print(f"Error in realtime_notifier: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


def handle_insert(record: Dict[str, Any]):
    """Handle new embedding insertion"""
    new_image = record.get("dynamodb", {}).get("NewImage", {})

    user_id = get_dynamodb_value(new_image.get("user_id"))
    status = get_dynamodb_value(new_image.get("status"))

    if status == "ACTIVE":
        # New enrollment success
        notification = {
            "type": "enrollment_success",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"User {user_id} successfully enrolled",
        }

        broadcast_notification(notification)


def handle_modify(record: Dict[str, Any]):
    """Handle embedding modification"""
    new_image = record.get("dynamodb", {}).get("NewImage", {})
    old_image = record.get("dynamodb", {}).get("OldImage", {})

    old_status = get_dynamodb_value(old_image.get("status"))
    new_status = get_dynamodb_value(new_image.get("status"))

    if old_status != new_status:
        user_id = get_dynamodb_value(new_image.get("user_id"))

        notification = {
            "type": "status_change",
            "user_id": user_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        broadcast_notification(notification)


def handle_remove(record: Dict[str, Any]):
    """Handle embedding removal"""
    old_image = record.get("dynamodb", {}).get("OldImage", {})

    user_id = get_dynamodb_value(old_image.get("user_id"))

    notification = {
        "type": "user_removed",
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"User {user_id} removed from system",
    }

    broadcast_notification(notification)


def get_dynamodb_value(attr: Dict[str, Any]) -> Any:
    """Extract value from DynamoDB attribute"""
    if not attr:
        return None

    if "S" in attr:
        return attr["S"]
    elif "N" in attr:
        return attr["N"]
    elif "BOOL" in attr:
        return attr["BOOL"]
    elif "B" in attr:
        return attr["B"]

    return None


def broadcast_notification(notification: Dict[str, Any]):
    """Broadcast notification to all WebSocket connections"""
    # Note: In production, you would:
    # 1. Query DynamoDB for active WebSocket connection IDs
    # 2. Send message to each connection
    # 3. Handle stale connections (remove from DB)

    print(f"Broadcasting notification: {json.dumps(notification)}")

    # For now, just log the notification
    # TODO: Implement WebSocket broadcasting with connection management

    # Example WebSocket send (requires connection ID):
    # if WEBSOCKET_ENDPOINT:
    #     global apigateway_management
    #     if not apigateway_management:
    #         apigateway_management = boto3.client(
    #             'apigatewaymanagementapi',
    #             endpoint_url=WEBSOCKET_ENDPOINT
    #         )
    #
    #     for connection_id in get_active_connections():
    #         try:
    #             apigateway_management.post_to_connection(
    #                 ConnectionId=connection_id,
    #                 Data=json.dumps(notification)
    #             )
    #         except:
    #             # Remove stale connection
    #             remove_connection(connection_id)
