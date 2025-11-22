"""
Auth Lambda Handler with Cognito Integration + Extended Profiles
Handles authentication, user registration, profile management, and admin operations
"""

from fastapi import FastAPI, HTTPException, Body, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError
import os
import sys

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.user_profiles import get_profile_manager
from shared.otp_manager import OTPManager

app = FastAPI(title="Face Recognition Auth API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cognito = boto3.client("cognito-idp", region_name=os.environ.get("AWS_REGION_VAL", "us-east-1"))
profile_manager = get_profile_manager()

# Environment variables
USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")


# ============================================================================
# Pydantic Models
# ============================================================================

class TokenResponse(BaseModel):
    access_token: str
    id_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    role: str
    groups: List[str]


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    gender: Optional[str] = None
    hometown: Optional[str] = None
    current_address: Optional[str] = None


class ProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    role: str
    gender: Optional[str] = None
    hometown: Optional[str] = None
    current_address: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    hometown: Optional[str] = None
    current_address: Optional[str] = None


class AdminUserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    enabled: Optional[bool] = None
    role: Optional[str] = None  # Admin, Staff, Guest


# ============================================================================
# Helper Functions
# ============================================================================

def get_user_from_token(authorization: str) -> dict:
    """Extract and verify user from Cognito JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Get user info from Cognito
        response = cognito.get_user(AccessToken=token)
        
        user_attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
        
        # Get user groups
        username = response['Username']
        groups_response = cognito.admin_list_groups_for_user(
            Username=username,
            UserPoolId=USER_POOL_ID
        )
        groups = [g['GroupName'] for g in groups_response.get('Groups', [])]
        
        return {
            'user_id': user_attributes.get('sub'),
            'username': username,
            'email': user_attributes.get('email'),
            'full_name': user_attributes.get('name', ''),
            'groups': groups,
            'role': groups[0] if groups else 'Guest'
        }
    except ClientError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_admin(authorization: str = Header(...)):
    """Dependency to require admin role"""
    user = get_user_from_token(authorization)
    if user['role'] != 'Admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.get("/auth/debug")
def debug_env():
    return {
        "region": os.environ.get("AWS_REGION"),
        "user_pool_id": USER_POOL_ID,
        "client_id": CLIENT_ID,
        "boto_region": cognito.meta.region_name
    }

@app.post("/auth/token")
def login(username: str = Body(...), password: str = Body(...)):
    """
    Login with Cognito and return tokens + profile data
    """
    print(f"Login attempt for user: {username}")
    print(f"Using Client ID: {CLIENT_ID}")
    print(f"Boto3 Region: {cognito.meta.region_name}")
    
    try:
        # Authenticate with Cognito
        print("Initiating auth with Cognito...")
        auth_params = {
            "USERNAME": username,
            "PASSWORD": password,
        }
        # Log masked password length
        print(f"Password length: {len(password)}")
        
        auth_response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_params,
        )
        print("Auth successful. Extracting tokens...")
        
        auth_result = auth_response["AuthenticationResult"]
        access_token = auth_result["AccessToken"]
        
        # Get user info
        print("Getting user info...")
        user_info = cognito.get_user(AccessToken=access_token)
        user_attributes = {attr['Name']: attr['Value'] for attr in user_info['UserAttributes']}
        print(f"User info retrieved: {user_attributes.get('sub')}")
        
        # Get user groups for RBAC
        print("Getting user groups...")
        groups_response = cognito.admin_list_groups_for_user(
            Username=username,
            UserPoolId=USER_POOL_ID
        )
        groups = [g['GroupName'] for g in groups_response.get('Groups', [])]
        role = groups[0] if groups else "Guest"
        print(f"User role: {role}, Groups: {groups}")
        
        return {
            "access_token": access_token,
            "id_token": auth_result.get("IdToken", ""),
            "refresh_token": auth_result.get("RefreshToken", ""),
            "token_type": "Bearer",
            "expires_in": auth_result.get("ExpiresIn", 3600),
            "role": role,
            "groups": groups
        }
    except ClientError as e:
        print(f"ClientError during login: {e}")
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        elif error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found")
        else:
            print(f"Unhandled ClientError: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during login")


# ============================================================================
# OTP Endpoints
# ============================================================================

class OTPRequest(BaseModel):
    email: EmailStr

@app.post("/auth/otp/send")
def send_otp(request: OTPRequest):
    """Generate and send OTP to email"""
    otp_manager = OTPManager()
    otp = otp_manager.generate_otp()
    
    if otp_manager.save_otp(request.email, otp):
        if otp_manager.send_email(request.email, otp):
            return {"success": True, "message": f"OTP sent to {request.email}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
    else:
        raise HTTPException(status_code=500, detail="Failed to save OTP")


@app.post("/auth/register")
def register(data: RegisterRequest):
    """
    Register new user using Cognito's built-in sign_up
    Cognito will send verification code to email automatically
    """
    try:
        # Sign up with Cognito (Cognito sends verification email automatically)
        response = cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=data.username,
            Password=data.password,
            UserAttributes=[
                {'Name': 'email', 'Value': data.email},
                {'Name': 'name', 'Value': data.full_name},
            ]
        )
        
        user_sub = response['UserSub']
        
        # Create extended profile
        profile_manager.create_profile(user_sub, {
            'gender': data.gender,
            'hometown': data.hometown,
            'current_address': data.current_address
        })
        
        return {
            "success": True,
            "message": "Registration successful. Please check your email for verification code.",
            "username": data.username,
            "user_id": user_sub
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            raise HTTPException(status_code=400, detail="Username already exists")
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(status_code=400, detail="Password does not meet requirements")
        else:
            raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/confirm-registration")
def confirm_registration(username: str = Body(...), code: str = Body(...)):
    """Confirm registration with verification code from email"""
    try:
        cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            ConfirmationCode=code
        )
        return {"success": True, "message": "Email verified successfully. You can now login."}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'CodeMismatchException':
            raise HTTPException(status_code=400, detail="Invalid verification code")
        elif error_code == 'ExpiredCodeException':
            raise HTTPException(status_code=400, detail="Verification code expired")
        else:
            raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Forgot Password Endpoints
# ============================================================================

class ForgotPasswordRequest(BaseModel):
    username: str

class ConfirmForgotPasswordRequest(BaseModel):
    username: str
    otp: str
    new_password: str

@app.post("/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    """Initiate forgot password flow (sends OTP via Cognito)"""
    try:
        cognito.forgot_password(
            ClientId=CLIENT_ID,
            Username=request.username
        )
        return {"success": True, "message": "Password reset code sent"}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/forgot-password/confirm")
def confirm_forgot_password(request: ConfirmForgotPasswordRequest):
    """Confirm password reset with OTP"""
    try:
        cognito.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=request.username,
            ConfirmationCode=request.otp,
            Password=request.new_password
        )
        return {"success": True, "message": "Password has been reset successfully"}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'CodeMismatchException':
            raise HTTPException(status_code=400, detail="Invalid verification code")
        elif error_code == 'ExpiredCodeException':
            raise HTTPException(status_code=400, detail="Verification code expired")
        else:
            raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Profile Management Endpoints
# ============================================================================

@app.get("/auth/profile")
def get_profile(authorization: str = Header(...)):
    """Get current user's profile (Cognito + DynamoDB data)"""
    user = get_user_from_token(authorization)
    
    # Get extended profile from DynamoDB
    profile_data = profile_manager.get_profile(user['user_id']) or {}
    
    return {
        "user_id": user['user_id'],
        "username": user['username'],
        "email": user['email'],
        "full_name": user['full_name'],
        "role": user['role'],
        "gender": profile_data.get('gender'),
        "hometown": profile_data.get('hometown'),
        "current_address": profile_data.get('current_address'),
        "created_at": profile_data.get('created_at'),
        "updated_at": profile_data.get('updated_at')
    }


@app.put("/auth/profile")
def update_profile(updates: ProfileUpdateRequest, authorization: str = Header(...)):
    """Update current user's profile"""
    user = get_user_from_token(authorization)
    
    # Update Cognito attributes if full_name changed
    if updates.full_name:
        try:
            cognito.admin_update_user_attributes(
                UserPoolId=USER_POOL_ID,
                Username=user['username'],
                UserAttributes=[
                    {'Name': 'name', 'Value': updates.full_name}
                ]
            )
        except ClientError as e:
            raise HTTPException(status_code=400, detail=f"Failed to update Cognito: {str(e)}")
    
    # Update extended fields in DynamoDB
    profile_updates = {}
    if updates.gender is not None:
        profile_updates['gender'] = updates.gender
    if updates.hometown is not None:
        profile_updates['hometown'] = updates.hometown
    if updates.current_address is not None:
        profile_updates['current_address'] = updates.current_address
    
    if profile_updates:
        profile_manager.update_profile(user['user_id'], profile_updates)
    
    # Return updated profile
    return get_profile(authorization)


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/auth/admin/users")
def list_users(admin_user: dict = Depends(require_admin)):
    """List all users (admin only)"""
    try:
        users = []
        paginator = cognito.get_paginator('list_users')
        
        for page in paginator.paginate(UserPoolId=USER_POOL_ID):
            for user in page['Users']:
                user_attributes = {attr['Name']: attr['Value'] for attr in user['Attributes']}
                user_id = user_attributes.get('sub')
                
                # Get groups
                groups_response = cognito.admin_list_groups_for_user(
                    Username=user['Username'],
                    UserPoolId=USER_POOL_ID
                )
                groups = [g['GroupName'] for g in groups_response.get('Groups', [])]
                
                # Get extended profile
                profile_data = profile_manager.get_profile(user_id) or {}
                
                users.append({
                    "user_id": user_id,
                    "username": user['Username'],
                    "email": user_attributes.get('email'),
                    "full_name": user_attributes.get('name', ''),
                    "enabled": user['Enabled'],
                    "status": user['UserStatus'],
                    "role": groups[0] if groups else 'Guest',
                    "groups": groups,
                    "gender": profile_data.get('gender'),
                    "hometown": profile_data.get('hometown'),
                    "current_address": profile_data.get('current_address'),
                    "created_at": profile_data.get('created_at'),
                    "updated_at": profile_data.get('updated_at')
                })
        
        return users
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/auth/admin/users/{username}")
def update_user(username: str, updates: AdminUserUpdateRequest, admin_user: dict = Depends(require_admin)):
    """Update user (admin only)"""
    try:
        # Get user to find user_id
        user_response = cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=username)
        user_attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
        user_id = user_attributes['sub']
        
        # Update Cognito attributes
        cognito_updates = []
        if updates.email:
            cognito_updates.append({'Name': 'email', 'Value': updates.email})
        if updates.full_name:
            cognito_updates.append({'Name': 'name', 'Value': updates.full_name})
        
        if cognito_updates:
            cognito.admin_update_user_attributes(
                UserPoolId=USER_POOL_ID,
                Username=username,
                UserAttributes=cognito_updates
            )
        
        # Update enabled status
        if updates.enabled is not None:
            if updates.enabled:
                cognito.admin_enable_user(UserPoolId=USER_POOL_ID, Username=username)
            else:
                cognito.admin_disable_user(UserPoolId=USER_POOL_ID, Username=username)
        
        # Update role (group membership)
        if updates.role:
            # Remove from all groups first
            current_groups = cognito.admin_list_groups_for_user(
                Username=username,
                UserPoolId=USER_POOL_ID
            )
            for group in current_groups.get('Groups', []):
                cognito.admin_remove_user_from_group(
                    UserPoolId=USER_POOL_ID,
                    Username=username,
                    GroupName=group['GroupName']
                )
            
            # Add to new group
            cognito.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=username,
                GroupName=updates.role
            )
        
        return {"success": True, "message": f"User {username} updated successfully"}
        
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/auth/admin/users/{username}")
def delete_user(username: str, admin_user: dict = Depends(require_admin)):
    """Delete user (admin only)"""
    try:
        # Get user_id before deletion
        user_response = cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=username)
        user_attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
        user_id = user_attributes['sub']
        
        # Delete from Cognito
        cognito.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        
        # Delete profile from DynamoDB
        profile_manager.delete_profile(user_id)
        
        return {"success": True, "message": f"User {username} deleted successfully"}
        
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Lambda Handler
# ============================================================================

handler = Mangum(app)
