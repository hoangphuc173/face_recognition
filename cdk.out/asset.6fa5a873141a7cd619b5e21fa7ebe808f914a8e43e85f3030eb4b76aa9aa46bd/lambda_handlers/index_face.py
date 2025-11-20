"""Lambda handler for face indexing step in enrollment."""

import json
import logging
import boto3
import os
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')
COLLECTION_ID = os.environ.get('REKOGNITION_COLLECTION_ID', 'face-recognition-collection')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Index face into Rekognition collection.
    
    Args:
        event: Input event with S3 path and user_id
        context: Lambda context
        
    Returns:
        Indexing result with face_id
    """
    try:
        logger.info(f"Indexing face into collection: {COLLECTION_ID}")
        
        # Extract parameters
        s3_path = event.get('s3_path', '')
        s3_key = event.get('s3_key', '')
        bucket = event.get('bucket', '')
        user_id = event.get('user_id', '')
        
        if not s3_key or not bucket:
            # Try to parse s3_path
            if s3_path.startswith('s3://'):
                parts = s3_path.replace('s3://', '').split('/', 1)
                bucket = parts[0]
                s3_key = parts[1] if len(parts) > 1 else ''
        
        if not s3_key or not bucket:
            raise ValueError("Missing S3 bucket or key")
        
        # Index face
        response = rekognition.index_faces(
            CollectionId=COLLECTION_ID,
            Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}},
            ExternalImageId=user_id,
            MaxFaces=1,
            QualityFilter='AUTO',
            DetectionAttributes=['ALL']
        )
        
        face_records = response.get('FaceRecords', [])
        
        if not face_records:
            logger.warning("⚠️ No faces detected in image")
            return {
                'success': False,
                'face_id': None,
                'message': 'No faces detected in image'
            }
        
        face_record = face_records[0]
        face_id = face_record['Face']['FaceId']
        confidence = face_record['Face']['Confidence']
        
        result = {
            'success': True,
            'face_id': face_id,
            'confidence': confidence,
            'external_image_id': user_id,
            'collection_id': COLLECTION_ID,
            'bounding_box': face_record['FaceDetail'].get('BoundingBox'),
            'quality': face_record['FaceDetail'].get('Quality')
        }
        
        logger.info(f"✅ Indexed face: {face_id} (confidence: {confidence})")
        return result
        
    except Exception as e:
        logger.error(f"❌ Indexing error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'face_id': None,
            'error': str(e)
        }
