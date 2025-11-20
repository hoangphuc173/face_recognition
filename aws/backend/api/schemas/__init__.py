"""
API Pydantic Schemas
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    environment: str
    database_status: str
    timestamp: str


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int


from typing import List, Optional, Any

class EnrollmentResponse(BaseModel):
    """Enrollment response model - matches app.py implementation."""
    success: bool
    user_name: str
    person_id: Optional[str]
    face_id: Optional[str]
    message: str
    duplicate_found: bool
    duplicate_info: Optional[dict] = None
    image_url: Optional[str] = None
    quality_score: Optional[float] = None
    processing_time_ms: float


class FaceMatch(BaseModel):
    """Schema for a single face match result."""
    person_id: str
    user_name: str
    gender: Optional[str] = None
    birth_year: Optional[str] = None
    hometown: Optional[str] = None
    residence: Optional[str] = None
    confidence: float
    similarity: float
    face_id: str
    match_time: str


class IdentificationResponse(BaseModel):
    """Identification response model - matches app.py implementation.
    
    Note: faces can be List[dict] or List[FaceMatch] depending on source.
    """
    success: bool
    faces_detected: int
    processing_time_ms: float
    faces: List[Any]  # Can be List[dict] from service or List[FaceMatch]


class PersonUpdate(BaseModel):
    """Schema for updating a person's information."""
    user_name: Optional[str] = None
    metadata: Optional[dict] = None


class PersonResponse(BaseModel):
    """Schema for a single person's full details - matches app.py PersonInfo."""
    folder_name: str
    person_id: Optional[str] = None  # Alias for folder_name
    user_name: str
    gender: Optional[str] = None
    birth_year: Optional[str] = None
    hometown: Optional[str] = None
    residence: Optional[str] = None
    embedding_count: int = 0
    created_at: str
    updated_at: str


class PeopleListResponse(BaseModel):
    """Response for listing all people."""
    total: int
    people: List[PersonResponse]


class DatabaseStats(BaseModel):
    """Schema for database statistics."""
    total_people: int
    total_embeddings: int
    storage_size_mb: float
