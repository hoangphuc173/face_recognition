"""
Authentication and Authorization Utilities
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

def is_admin(event: Dict) -> bool:
    """Check if the user is in the 'admin' group from Cognito token."""
    try:
        # API Gateway with Cognito Authorizer passes claims here
        groups = event["requestContext"]["authorizer"]["claims"].get("cognito:groups", "")
        
        # The 'cognito:groups' claim can be a string or a list
        if isinstance(groups, str):
            return "admin" in groups.split(',')
        elif isinstance(groups, list):
            return "admin" in groups
            
        return False
    except (KeyError, AttributeError):
        # This will happen if:
        # 1. The API endpoint is not protected by a Cognito Authorizer.
        # 2. The token does not contain the 'cognito:groups' claim.
        logger.warning("Could not verify admin status from event. Defaulting to non-admin.")
        return False

