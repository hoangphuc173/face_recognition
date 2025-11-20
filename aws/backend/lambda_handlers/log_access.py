"""Lambda handler for access logging step."""

import json
import logging
import boto3
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
ACCESS_LOGS_TABLE = os.environ.get('ACCESS_LOGS_TABLE', 'face-recognition-access-logs')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Log access event to DynamoDB.
    
    Args:
        event: Input event with identification/enrollment details
        context: Lambda context
        
    Returns:
        Logging result
    """
    try:
        logger.info("Logging access event")
        
        table = dynamodb.Table(ACCESS_LOGS_TABLE)
        
        # Extract event details
        event_type = event.get('event_type', 'identification')
        users = event.get('metadata', {}).get('users', [])
        detection = event.get('detection', {}).get('Payload', {})
        search = event.get('search', {}).get('Payload', {})
        timestamp = event.get('timestamp', datetime.utcnow().isoformat())
        
        # Create log entries for each identified user
        log_ids = []
        for user in users:
            log_id = str(uuid.uuid4())
            ttl = int((datetime.utcnow() + timedelta(days=180)).timestamp())  # 6 months
            
            item = {
                'log_id': log_id,
                'timestamp': timestamp,
                'event_type': event_type,
                'user_id': user.get('person_id'),
                'user_name': user.get('user_name'),
                'confidence_score': float(user.get('confidence', 0.0)),
                'similarity': float(user.get('similarity', 0.0)),
                'status': 'success',
                'ttl': ttl,
                'source_location': event.get('source_location', 'unknown'),
                'faces_detected': detection.get('faces_detected', 0)
            }
            
            table.put_item(Item=item)
            log_ids.append(log_id)
            logger.info(f"✅ Logged access for user: {user.get('user_name')}")
        
        # Also log if no match found
        if not users and event_type == 'identification':
            log_id = str(uuid.uuid4())
            ttl = int((datetime.utcnow() + timedelta(days=180)).timestamp())
            
            item = {
                'log_id': log_id,
                'timestamp': timestamp,
                'event_type': 'identification_no_match',
                'status': 'no_match',
                'ttl': ttl,
                'source_location': event.get('source_location', 'unknown'),
                'faces_detected': detection.get('faces_detected', 0)
            }
            
            table.put_item(Item=item)
            log_ids.append(log_id)
            logger.info("✅ Logged no-match event")
        
        result = {
            'success': True,
            'log_ids': log_ids,
            'log_count': len(log_ids)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Logging error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'log_ids': [],
            'log_count': 0,
            'error': str(e)
        }
