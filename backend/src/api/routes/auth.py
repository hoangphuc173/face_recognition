"""Authentication routes for JWT token generation and user management."""

import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

# Simple settings for standalone operation
class Settings:
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 30  # minutes

router = APIRouter()
settings = Settings()

# Use bcrypt with sha256 for better compatibility
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# In-memory user database (replace with real database in production)
FAKE_USERS_DB: Dict[str, dict] = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2h/xmDq7Ei",  # admin123
        "disabled": False,
        "role": "admin",
        "gender": None,
        "hometown": None,
        "current_address": None,
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }
}


# ============================================================================
# Helper Functions
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str) -> Optional[dict]:
    """Retrieve a user from the database."""
    return FAKE_USERS_DB.get(username)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify current user is admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================================================
# Pydantic Models
# ============================================================================

class TokenResponse(BaseModel):
    """Response model for access token."""
    access_token: str
    token_type: str
    expires_in: int


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    username: str
    full_name: str
    email: EmailStr
    password: str
    gender: Optional[str] = None
    hometown: Optional[str] = None
    current_address: Optional[str] = None


class RegisterResponse(BaseModel):
    """Response model for user registration."""
    success: bool
    message: str
    username: str
    role: str


class UserProfile(BaseModel):
    """User profile response model."""
    username: str
    full_name: str
    email: str
    role: str
    gender: Optional[str] = None
    hometown: Optional[str] = None
    current_address: Optional[str] = None
    created_at: int
    updated_at: int


class ProfileUpdateRequest(BaseModel):
    """Request model for profile update."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    hometown: Optional[str] = None
    current_address: Optional[str] = None


class AdminUserUpdateRequest(BaseModel):
    """Admin request model for updating any user."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None
    gender: Optional[str] = None
    hometown: Optional[str] = None
    current_address: Optional[str] = None


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT access token."""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    access_token_expires = timedelta(minutes=settings.jwt_expiration)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role", "user")},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }


@router.post("/register", response_model=RegisterResponse)
async def register_user(data: RegisterRequest):
    """Register a new user account."""
    # Validation
    if len(data.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    if len(data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    if data.username in FAKE_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create user
    current_time = int(time.time())
    hashed_password = pwd_context.hash(data.password)
    
    # First user after admin becomes admin (for testing), otherwise user
    role = "admin" if len(FAKE_USERS_DB) == 1 else "user"
    
    FAKE_USERS_DB[data.username] = {
        "username": data.username,
        "full_name": data.full_name,
        "email": data.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "role": role,
        "gender": data.gender,
        "hometown": data.hometown,
        "current_address": data.current_address,
        "created_at": current_time,
        "updated_at": current_time,
    }
    
    return {
        "success": True,
        "message": f"User '{data.username}' registered successfully",
        "username": data.username,
        "role": role,
    }


# ============================================================================
# Profile Management Endpoints
# ============================================================================

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile."""
    return {
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user.get("role", "user"),
        "gender": current_user.get("gender"),
        "hometown": current_user.get("hometown"),
        "current_address": current_user.get("current_address"),
        "created_at": current_user.get("created_at", int(time.time())),
        "updated_at": current_user.get("updated_at", int(time.time())),
    }


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile."""
    username = current_user["username"]
    user = FAKE_USERS_DB[username]
    
    # Update fields
    if profile_data.full_name is not None:
        user["full_name"] = profile_data.full_name
    if profile_data.email is not None:
        user["email"] = profile_data.email
    if profile_data.gender is not None:
        user["gender"] = profile_data.gender
    if profile_data.hometown is not None:
        user["hometown"] = profile_data.hometown
    if profile_data.current_address is not None:
        user["current_address"] = profile_data.current_address
    
    user["updated_at"] = int(time.time())
    
    return {
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "gender": user.get("gender"),
        "hometown": user.get("hometown"),
        "current_address": user.get("current_address"),
        "created_at": user.get("created_at", int(time.time())),
        "updated_at": user["updated_at"],
    }


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.get("/admin/users", response_model=List[UserProfile])
async def list_users(current_user: dict = Depends(get_current_admin_user)):
    """List all users (admin only)."""
    users = []
    for user in FAKE_USERS_DB.values():
        users.append({
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user.get("role", "user"),
            "gender": user.get("gender"),
            "hometown": user.get("hometown"),
            "current_address": user.get("current_address"),
            "created_at": user.get("created_at", int(time.time())),
            "updated_at": user.get("updated_at", int(time.time())),
        })
    return users


@router.get("/admin/users/{username}", response_model=UserProfile)
async def get_user_by_username(
    username: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Get user by username (admin only)."""
    user = get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "gender": user.get("gender"),
        "hometown": user.get("hometown"),
        "current_address": user.get("current_address"),
        "created_at": user.get("created_at", int(time.time())),
        "updated_at": user.get("updated_at", int(time.time())),
    }


@router.put("/admin/users/{username}", response_model=UserProfile)
async def update_user(
    username: str,
    user_data: AdminUserUpdateRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """Update any user (admin only)."""
    user = FAKE_USERS_DB.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_data.full_name is not None:
        user["full_name"] = user_data.full_name
    if user_data.email is not None:
        user["email"] = user_data.email
    if user_data.role is not None:
        user["role"] = user_data.role
    if user_data.disabled is not None:
        user["disabled"] = user_data.disabled
    if user_data.gender is not None:
        user["gender"] = user_data.gender
    if user_data.hometown is not None:
        user["hometown"] = user_data.hometown
    if user_data.current_address is not None:
        user["current_address"] = user_data.current_address
    
    user["updated_at"] = int(time.time())
    
    return {
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "gender": user.get("gender"),
        "hometown": user.get("hometown"),
        "current_address": user.get("current_address"),
       "created_at": user.get("created_at", int(time.time())),
        "updated_at": user["updated_at"],
    }


@router.delete("/admin/users/{username}")
async def delete_user(
    username: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Delete user (admin only)."""
    if username not in FAKE_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting yourself
    if username == current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    del FAKE_USERS_DB[username]
    
    return {"success": True, "message": f"User '{username}' deleted successfully"}
