"""Lambda handler for validation step in workflows."""

import json
import logging
import base64
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Validate input for face recognition workflows.
    
    Args:
        event: Input event containing image data and mode
        context: Lambda context
        
    Returns:
        Validation result
    """
    try:
        logger.info(f"Validation event: {json.dumps(event, default=str)}")
        
        # Extract input
        input_data = event.get('input', event)
        mode = input_data.get('mode', 'identification')
        
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'mode': mode
        }
        
        # Check required fields
        if 'image' not in input_data:
            result['errors'].append('Missing required field: image')
        
        # Validate image data
        image_data = input_data.get('image', '')
        if image_data:
            try:
                # Try to decode base64
                if isinstance(image_data, str):
                    decoded = base64.b64decode(image_data)
                    if len(decoded) == 0:
                        result['errors'].append('Image data is empty')
                    elif len(decoded) > 10 * 1024 * 1024:  # 10MB limit
                        result['errors'].append('Image size exceeds 10MB limit')
                else:
                    result['errors'].append('Image must be base64 encoded string')
            except Exception as e:
                result['errors'].append(f'Invalid base64 encoding: {str(e)}')
        
        # Mode-specific validation
        if mode == 'enrollment':
            if 'user_id' not in input_data:
                result['errors'].append('Missing required field for enrollment: user_id')
            if 'user_name' not in input_data:
                result['errors'].append('Missing required field for enrollment: user_name')
        
        # Check thresholds
        threshold = input_data.get('threshold', 80.0)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 100:
            result['warnings'].append(f'Invalid threshold {threshold}, using default 80.0')
            input_data['threshold'] = 80.0
        
        # Set valid flag
        result['valid'] = len(result['errors']) == 0
        
        if result['valid']:
            logger.info("✅ Validation passed")
        else:
            logger.warning(f"⚠️ Validation failed: {result['errors']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Validation error: {str(e)}", exc_info=True)
        return {
            'valid': False,
            'errors': [f'Validation exception: {str(e)}'],
            'warnings': []
        }
