"""Lambda handler for metadata retrieval step."""

import json
import logging
import boto3
import os
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
PEOPLE_TABLE = os.environ.get('PEOPLE_TABLE', 'face-recognition-people')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Get user metadata from DynamoDB.
    
    Args:
        event: Input event with matches
        context: Lambda context
        
    Returns:
        User metadata for matched faces
    """
    try:
        logger.info("Retrieving user metadata")
        
        matches = event.get('matches', [])
        if not matches:
            logger.info("No matches to retrieve metadata for")
            return {
                'success': True,
                'users': [],
                'user_count': 0
            }
        
        table = dynamodb.Table(PEOPLE_TABLE)
        users = []
        
        # Batch get items
        person_ids = [m.get('external_image_id') for m in matches if m.get('external_image_id')]
        
        for person_id in person_ids:
            try:
                response = table.get_item(Key={'person_id': person_id})
                if 'Item' in response:
                    user = response['Item']
                    # Add similarity from match
                    match = next((m for m in matches if m.get('external_image_id') == person_id), {})
                    user['similarity'] = match.get('similarity', 0.0)
                    user['confidence'] = match.get('confidence', 0.0)
                    users.append(user)
                else:
                    logger.warning(f"⚠️ Person not found: {person_id}")
            except Exception as e:
                logger.error(f"❌ Error getting user {person_id}: {str(e)}")
        
        result = {
            'success': True,
            'users': users,
            'user_count': len(users)
        }
        
        logger.info(f"✅ Retrieved metadata for {len(users)} user(s)")
        return result
        
    except Exception as e:
        logger.error(f"❌ Metadata retrieval error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'users': [],
            'user_count': 0,
            'error': str(e)
        }
