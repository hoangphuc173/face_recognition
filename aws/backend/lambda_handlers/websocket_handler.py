"""
WebSocket Handler for Realtime PyQt App Sync (báo cáo 5.1)
"""

import os
import json
import boto3
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# AWS clients
apigateway_management = None  # Initialized per connection
dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
CONNECTIONS_TABLE = os.environ.get('DYNAMODB_CONNECTIONS_TABLE', 'WebSocketConnections')
STAGE = os.environ.get('STAGE', 'prod')


class WebSocketManager:
    """Quản lý WebSocket connections cho realtime updates"""
    
    def __init__(self, endpoint_url: Optional[str] = None):
        self.connections_table = dynamodb.Table(CONNECTIONS_TABLE)
        
        if endpoint_url:
            self.api_client = boto3.client(
                'apigatewaymanagementapi',
                endpoint_url=endpoint_url
            )
        else:
            self.api_client = None
    
    def store_connection(
        self,
        connection_id: str,
        user_id: Optional[str] = None,
        client_type: str = 'unknown',
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Lưu connection info khi client connect
        
        Args:
            connection_id: WebSocket connection ID
            user_id: User ID nếu đã authenticate
            client_type: 'pyqt', 'web', 'mobile'
            metadata: Additional metadata
        
        Returns:
            Success status
        """
        
        try:
            item = {
                'connection_id': connection_id,
                'connected_at': datetime.utcnow().isoformat(),
                'user_id': user_id or 'anonymous',
                'client_type': client_type,
                'metadata': json.dumps(metadata or {}),
                'ttl': int((datetime.utcnow().timestamp()) + 86400)  # 24h TTL
            }
            
            self.connections_table.put_item(Item=item)
            logger.info(f"Stored connection {connection_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store connection: {e}")
            return False
    
    def remove_connection(self, connection_id: str) -> bool:
        """Xóa connection khi client disconnect"""
        
        try:
            self.connections_table.delete_item(
                Key={'connection_id': connection_id}
            )
            logger.info(f"Removed connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove connection: {e}")
            return False
    
    def get_user_connections(self, user_id: str) -> list:
        """Lấy tất cả connections của một user"""
        
        try:
            response = self.connections_table.scan(
                FilterExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Failed to get user connections: {e}")
            return []
    
    def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Gửi message tới một connection cụ thể
        
        Args:
            connection_id: Target connection ID
            message: Message data
        
        Returns:
            Success status
        """
        
        if not self.api_client:
            logger.error("API client not initialized")
            return False
        
        try:
            self.api_client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message).encode('utf-8')
            )
            
            logger.info(f"Sent message to {connection_id}")
            return True
            
        except self.api_client.exceptions.GoneException:
            # Connection đã đóng
            logger.warning(f"Connection {connection_id} is gone, removing")
            self.remove_connection(connection_id)
            return False
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def broadcast_to_user(
        self,
        user_id: str,
        message: Dict[str, Any]
    ) -> int:
        """
        Broadcast message tới tất cả connections của user
        
        Args:
            user_id: Target user ID
            message: Message data
        
        Returns:
            Number of successful sends
        """
        
        connections = self.get_user_connections(user_id)
        success_count = 0
        
        for conn in connections:
            if self.send_to_connection(conn['connection_id'], message):
                success_count += 1
        
        logger.info(f"Broadcasted to {success_count}/{len(connections)} connections for user {user_id}")
        return success_count
    
    def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """
        Broadcast tới tất cả active connections
        (Dùng cho system announcements)
        """
        
        try:
            response = self.connections_table.scan()
            connections = response.get('Items', [])
            
            success_count = 0
            for conn in connections:
                if self.send_to_connection(conn['connection_id'], message):
                    success_count += 1
            
            logger.info(f"Broadcasted to {success_count}/{len(connections)} total connections")
            return success_count
            
        except Exception as e:
            logger.error(f"Failed to broadcast: {e}")
            return 0


def lambda_handler(event, context):
    """
    Lambda handler cho WebSocket events
    
    Routes:
    - $connect: Client kết nối
    - $disconnect: Client ngắt kết nối
    - $default: Custom actions (subscribe, identify_result, etc.)
    """
    
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')
    domain_name = event.get('requestContext', {}).get('domainName')
    stage = event.get('requestContext', {}).get('stage')
    
    # Initialize API client với endpoint
    endpoint_url = f"https://{domain_name}/{stage}"
    ws_manager = WebSocketManager(endpoint_url)
    
    try:
        if route_key == '$connect':
            # Handle connection
            query_params = event.get('queryStringParameters', {}) or {}
            user_id = query_params.get('user_id')
            client_type = query_params.get('client_type', 'unknown')
            
            success = ws_manager.store_connection(
                connection_id,
                user_id,
                client_type,
                metadata={'query_params': query_params}
            )
            
            if success:
                # Send welcome message
                welcome_msg = {
                    'type': 'connection_established',
                    'timestamp': datetime.utcnow().isoformat(),
                    'connection_id': connection_id,
                    'message': 'Connected to Face Recognition WebSocket API'
                }
                ws_manager.send_to_connection(connection_id, welcome_msg)
            
            return {'statusCode': 200}
        
        elif route_key == '$disconnect':
            # Handle disconnection
            ws_manager.remove_connection(connection_id)
            return {'statusCode': 200}
        
        elif route_key == '$default':
            # Handle custom actions
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'ping':
                # Health check
                response = {
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                }
                ws_manager.send_to_connection(connection_id, response)
            
            elif action == 'subscribe':
                # Subscribe to updates
                user_id = body.get('user_id')
                
                # Update connection với subscription info
                ws_manager.store_connection(
                    connection_id,
                    user_id,
                    client_type='pyqt',
                    metadata={'subscribed': True, 'topics': body.get('topics', [])}
                )
                
                response = {
                    'type': 'subscription_confirmed',
                    'user_id': user_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                ws_manager.send_to_connection(connection_id, response)
            
            elif action == 'get_status':
                # Get system status
                response = {
                    'type': 'system_status',
                    'status': 'operational',
                    'timestamp': datetime.utcnow().isoformat(),
                    'connection_id': connection_id
                }
                ws_manager.send_to_connection(connection_id, response)
            
            else:
                # Unknown action
                error_msg = {
                    'type': 'error',
                    'error': f'Unknown action: {action}',
                    'timestamp': datetime.utcnow().isoformat()
                }
                ws_manager.send_to_connection(connection_id, error_msg)
            
            return {'statusCode': 200}
        
        else:
            logger.warning(f"Unknown route: {route_key}")
            return {'statusCode': 400}
    
    except Exception as e:
        logger.error(f"WebSocket handler error: {str(e)}")
        return {'statusCode': 500}


def notify_identification_result(user_id: str, result: Dict[str, Any], endpoint_url: str):
    """
    Helper function để notify PyQt app về kết quả identification
    Gọi từ identification Lambda sau khi xử lý xong
    
    Args:
        user_id: User ID
        result: Identification result
        endpoint_url: WebSocket API endpoint
    """
    
    ws_manager = WebSocketManager(endpoint_url)
    
    message = {
        'type': 'identification_result',
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': result.get('user_id'),
        'confidence': result.get('confidence'),
        'name': result.get('name'),
        'department': result.get('department'),
        'status': 'success' if result.get('user_id') else 'not_found'
    }
    
    # Broadcast tới tất cả connections của user
    count = ws_manager.broadcast_to_user(user_id, message)
    logger.info(f"Notified {count} connections about identification result")


def notify_enrollment_complete(user_id: str, enrollment_data: Dict[str, Any], endpoint_url: str):
    """
    Notify về enrollment completion
    
    Args:
        user_id: User ID
        enrollment_data: Enrollment result
        endpoint_url: WebSocket API endpoint
    """
    
    ws_manager = WebSocketManager(endpoint_url)
    
    message = {
        'type': 'enrollment_complete',
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'face_count': enrollment_data.get('face_count', 0),
        'status': 'success'
    }
    
    count = ws_manager.broadcast_to_user(user_id, message)
    logger.info(f"Notified {count} connections about enrollment completion")


def broadcast_system_alert(message: str, severity: str, endpoint_url: str):
    """
    Broadcast system alert tới tất cả clients
    
    Args:
        message: Alert message
        severity: 'info', 'warning', 'error'
        endpoint_url: WebSocket API endpoint
    """
    
    ws_manager = WebSocketManager(endpoint_url)
    
    alert_msg = {
        'type': 'system_alert',
        'timestamp': datetime.utcnow().isoformat(),
        'message': message,
        'severity': severity
    }
    
    count = ws_manager.broadcast_to_all(alert_msg)
    logger.info(f"Broadcasted alert to {count} connections")
