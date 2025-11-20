"""Authentication routes for JWT token generation."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from ..schemas import TokenResponse
from ...utils.config import get_settings

router = APIRouter()
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In a real application, this would be a database call.
# Hashed password for 'admin' is 'admin123'
# Generated with: python -c "from passlib.hash import bcrypt; print(bcrypt.hash('admin123'))"
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2h/xmDq7Ei",  # admin123
        "disabled": False,
    }
}

def verify_password(plain_password, hashed_password):
    """Verify a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    """Retrieve a user from the fake database."""
    if username in FAKE_USERS_DB:
        user_dict = FAKE_USERS_DB[username]
        return user_dict
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return a JWT access token."""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.jwt_expiration)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    username: str
    full_name: str
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    """Response model for user registration."""
    success: bool
    message: str
    username: str
    role: str = "user"


@router.post("/register", response_model=RegisterResponse)
async def register_user(data: RegisterRequest):
    """Register a new user account with 'user' role by default."""
    # Validate username length
    if len(data.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long",
        )
    
    # Validate password length
    if len(data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long",
        )
    
    # Check if username already exists
    if data.username in FAKE_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    # Hash the password
    hashed_password = pwd_context.hash(data.password)
    
    # Add new user to database (with 'user' role by default)
    FAKE_USERS_DB[data.username] = {
        "username": data.username,
        "full_name": data.full_name,
        "email": data.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "role": "user",  # Default role
    }
    
    return {
        "success": True,
        "message": f"User '{data.username}' registered successfully",
        "username": data.username,
        "role": "user",
    }
