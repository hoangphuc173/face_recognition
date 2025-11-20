"""Lambda handler for duplicate check step in enrollment."""

import json
import logging
import base64
import boto3
import os
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekognition = boto3.client('rekognition')
COLLECTION_ID = os.environ.get('REKOGNITION_COLLECTION_ID', 'face-recognition-collection')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Check for duplicate faces in collection.
    
    Args:
        event: Input event with image and threshold
        context: Lambda context
        
    Returns:
        Duplicate check result
    """
    try:
        logger.info("Checking for duplicate faces")
        
        # Extract parameters
        image_data = event.get('image', '')
        threshold = float(event.get('threshold', 95.0))  # Higher threshold for duplicates
        
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Search for similar faces
        response = rekognition.search_faces_by_image(
            CollectionId=COLLECTION_ID,
            Image={'Bytes': image_bytes},
            MaxFaces=5,
            FaceMatchThreshold=threshold
        )
        
        matches = response.get('FaceMatches', [])
        
        result = {
            'success': True,
            'duplicate_found': len(matches) > 0,
            'match_count': len(matches),
            'matches': [
                {
                    'face_id': match['Face']['FaceId'],
                    'external_image_id': match['Face']['ExternalImageId'],
                    'similarity': match['Similarity']
                }
                for match in matches
            ],
            'threshold': threshold
        }
        
        if matches:
            logger.warning(f"⚠️ Found {len(matches)} duplicate(s) with similarity >{threshold}%")
        else:
            logger.info("✅ No duplicates found")
        
        return result
        
    except rekognition.exceptions.InvalidParameterException as e:
        logger.info("✅ No faces detected - not a duplicate")
        return {
            'success': True,
            'duplicate_found': False,
            'match_count': 0,
            'matches': [],
            'message': 'No faces detected in image'
        }
    except Exception as e:
        logger.error(f"❌ Duplicate check error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'duplicate_found': False,
            'match_count': 0,
            'matches': [],
            'error': str(e)
        }
