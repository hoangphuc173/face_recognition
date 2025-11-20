"""Lambda handler for face detection step."""

import json
import logging
import base64
import boto3
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekognition = boto3.client('rekognition')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Detect faces in image using Rekognition.
    
    Args:
        event: Input event with image data
        context: Lambda context
        
    Returns:
        Detection result with faces found
    """
    try:
        logger.info("Starting face detection")
        
        # Extract image
        image_data = event.get('image', '')
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Call Rekognition
        response = rekognition.detect_faces(
            Image={'Bytes': image_bytes},
            Attributes=['ALL']
        )
        
        faces = response.get('FaceDetails', [])
        
        result = {
            'success': True,
            'faces_detected': len(faces),
            'faces': [
                {
                    'bounding_box': face.get('BoundingBox'),
                    'confidence': face.get('Confidence'),
                    'landmarks': face.get('Landmarks'),
                    'pose': face.get('Pose'),
                    'quality': face.get('Quality'),
                    'emotions': face.get('Emotions', [])[:3]  # Top 3 emotions
                }
                for face in faces
            ]
        }
        
        logger.info(f"✅ Detected {len(faces)} face(s)")
        return result
        
    except Exception as e:
        logger.error(f"❌ Detection error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'faces_detected': 0,
            'faces': [],
            'error': str(e)
        }
