"""Lambda handler for S3 upload step in enrollment."""

import json
import logging
import base64
import boto3
import os
import uuid
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('RAW_IMAGES_BUCKET', 'face-recognition-images')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Upload image to S3.
    
    Args:
        event: Input event with image and user_id
        context: Lambda context
        
    Returns:
        Upload result with S3 path
    """
    try:
        logger.info(f"Uploading image to S3 bucket: {BUCKET_NAME}")
        
        # Extract data
        image_data = event.get('image', '')
        user_id = event.get('user_id', f'user_{uuid.uuid4().hex[:8]}')
        
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Generate S3 key
        timestamp = uuid.uuid4().hex[:8]
        s3_key = f"enrollments/{user_id}/{timestamp}.jpg"
        
        # Upload to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=image_bytes,
            ContentType='image/jpeg',
            ServerSideEncryption='AES256'
        )
        
        s3_url = f"s3://{BUCKET_NAME}/{s3_key}"
        
        result = {
            'success': True,
            's3_key': s3_key,
            's3_url': s3_url,
            'bucket': BUCKET_NAME,
            'size_bytes': len(image_bytes)
        }
        
        logger.info(f"✅ Uploaded to {s3_url}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}", exc_info=True)
        return {
            'success': False,
            's3_key': None,
            's3_url': None,
            'error': str(e)
        }
