"""
User Profile Management Module
Handles CRUD operations for extended user profile data in DynamoDB
"""

import boto3
import os
import time
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError


class UserProfileManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'ap-southeast-1'))
        self.table_name = os.environ.get('USER_PROFILES_TABLE', 'UserProfiles')
        self.table = self.dynamodb.Table(self.table_name)
    
    def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user profile in DynamoDB
        
        Args:
            user_id: Cognito user ID (sub claim from JWT)
            profile_data: Dict with optional fields: gender, hometown, current_address
        
        Returns:
            Created profile data
        """
        current_time = int(time.time())
        
        item = {
            'UserId': user_id,
            'gender': profile_data.get('gender'),
            'hometown': profile_data.get('hometown'),
            'current_address': profile_data.get('current_address'),
            'created_at': current_time,
            'updated_at': current_time
        }
        
        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}
        
        try:
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            raise Exception(f"Failed to create profile: {str(e)}")
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user profile from DynamoDB
        
        Args:
            user_id: Cognito user ID
        
        Returns:
            Profile data or None if not found
        """
        try:
            response = self.table.get_item(Key={'UserId': user_id})
            return response.get('Item')
        except ClientError as e:
            raise Exception(f"Failed to get profile: {str(e)}")
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile fields
        
        Args:
            user_id: Cognito user ID
            updates: Dict with fields to update (gender, hometown, current_address)
        
        Returns:
            Updated profile data
        """
        current_time = int(time.time())
        
        # Build update expression
        update_parts = []
        expr_attr_names = {}
        expr_attr_values = {}
        
        for key, value in updates.items():
            if key in ['gender', 'hometown', 'current_address'] and value is not None:
                update_parts.append(f"#{key} = :{key}")
                expr_attr_names[f"#{key}"] = key
                expr_attr_values[f":{key}"] = value
        
        # Always update timestamp
        update_parts.append("#updated_at = :updated_at")
        expr_attr_names["#updated_at"] = "updated_at"
        expr_attr_values[":updated_at"] = current_time
        
        if not update_parts:
            # No updates provided
            return self.get_profile(user_id) or {}
        
        update_expression = "SET " + ", ".join(update_parts)
        
        try:
            response = self.table.update_item(
                Key={'UserId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            return response.get('Attributes', {})
        except ClientError as e:
            raise Exception(f"Failed to update profile: {str(e)}")
    
    def delete_profile(self, user_id: str) -> bool:
        """
        Delete user profile from DynamoDB
        
        Args:
            user_id: Cognito user ID
        
        Returns:
            True if deleted successfully
        """
        try:
            self.table.delete_item(Key={'UserId': user_id})
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete profile: {str(e)}")


# Singleton instance for Lambda
_profile_manager = None

def get_profile_manager() -> UserProfileManager:
    """Get or create UserProfileManager singleton"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = UserProfileManager()
    return _profile_manager
