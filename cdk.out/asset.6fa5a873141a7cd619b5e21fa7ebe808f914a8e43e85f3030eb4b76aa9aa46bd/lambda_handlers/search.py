"""Lambda handler for face search step."""

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
    """Search faces in Rekognition collection.
    
    Args:
        event: Input event with image and threshold
        context: Lambda context
        
    Returns:
        Search result with matches
    """
    try:
        logger.info(f"Searching faces in collection: {COLLECTION_ID}")
        
        # Extract parameters
        image_data = event.get('image', '')
        threshold = float(event.get('threshold', 80.0))
        max_faces = int(event.get('max_faces', 5))
        
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Search in collection
        response = rekognition.search_faces_by_image(
            CollectionId=COLLECTION_ID,
            Image={'Bytes': image_bytes},
            MaxFaces=max_faces,
            FaceMatchThreshold=threshold
        )
        
        matches = []
        for match in response.get('FaceMatches', []):
            face = match.get('Face', {})
            matches.append({
                'face_id': face.get('FaceId'),
                'external_image_id': face.get('ExternalImageId'),
                'similarity': match.get('Similarity'),
                'confidence': face.get('Confidence')
            })
        
        result = {
            'success': True,
            'matches': matches,
            'match_count': len(matches),
            'collection_id': COLLECTION_ID
        }
        
        logger.info(f"✅ Found {len(matches)} match(es)")
        return result
        
    except rekognition.exceptions.InvalidParameterException as e:
        logger.warning(f"⚠️ No faces in image: {str(e)}")
        return {
            'success': True,
            'matches': [],
            'match_count': 0,
            'message': 'No faces detected in image'
        }
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'matches': [],
            'match_count': 0,
            'error': str(e)
        }
