"""FastAPI application cho Face Recognition System

NOTE: This file defines routes directly. Alternative route modules exist in
api/routes/ but are not currently integrated. To use them, add:
    from api.routes import enroll, identify, people, auth, health
    app.include_router(enroll.router, prefix="/api/v1", tags=["enrollment"])
    app.include_router(identify.router, prefix="/api/v1", tags=["identification"])
    app.include_router(people.router, prefix="/api/v1", tags=["people"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
    app.include_router(health.router, tags=["health"])
"""

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    Depends,
    status,
    Request,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uvicorn
from datetime import datetime, timezone
import psutil

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.core.enrollment_service import EnrollmentService  # noqa: E402
from backend.core.identification_service import IdentificationService  # noqa: E402
from backend.core.database_manager import DatabaseManager  # noqa: E402
from backend.aws.s3_client import S3Client  # noqa: E402
from backend.aws.rekognition_client import RekognitionClient  # noqa: E402
from backend.aws.dynamodb_client import DynamoDBClient  # noqa: E402
from backend.utils.config import settings  # noqa: E402
from backend.utils.logger import setup_logger  # noqa: E402
from .schemas import (  # noqa: E402
    EnrollmentResponse,
    IdentificationResponse,
    FaceMatch,
)

xray_enabled = False
if settings.enable_xray:
    try:
        from aws_xray_sdk.core import patch_all, xray_recorder
        from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

        patch_all()  # patch boto3, requests, etc.
        xray_enabled = True
    except ImportError:
        xray_enabled = False

# Setup logger
logger = setup_logger("api", level=settings.log_level, json_format=True)

# Initialize FastAPI
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Professional Face Recognition API

    This API provides enterprise-grade face recognition capabilities powered by AWS Rekognition.

    ### Features:
    * **Face Enrollment**: Register new faces with metadata
    * **Face Identification**: Identify known faces in images
    * **Database Management**: Manage enrolled people and their data
    * **Real-time Telemetry**: Monitor system performance

    ### Authentication:
    * **Cognito JWT**: AWS Cognito authentication (production)
    * **API Key**: Header-based authentication for automation
    * **Anonymous**: Local development mode

    ### Admin Operations:
    Some endpoints require administrator privileges (admin group membership).
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Face Recognition System Support",
        "email": "support@facerecog.example.com",
    },
    license_info={
        "name": "Proprietary",
    },
)

# X-Ray middleware
if xray_enabled:
    xray_recorder.configure(service=settings.app_name)
    app.add_middleware(XRayMiddleware, recorder=xray_recorder)
    logger.info("AWS X-Ray tracing enabled for API service")

# CORS
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Instrument the app for Prometheus
Instrumentator().instrument(app).expose(app)

# Import dependencies module for shared services
from .dependencies import (
    initialize_clients,
    get_enrollment_service,
    get_identification_service,
    get_database_manager,
)

# Startup event to initialize shared AWS clients
@app.on_event("startup")
async def startup_event():
    """Initialize AWS clients and services on application startup."""
    logger.info("🚀 Application startup: Initializing AWS clients...")
    initialize_clients()
    logger.info("✅ Application startup complete")

# Legacy variables for backward compatibility with inline endpoints
# These will be populated after startup event
enrollment_service = None
identification_service = None
db_manager = None

def get_services():
    """Get services after they've been initialized in startup event."""
    global enrollment_service, identification_service, db_manager
    if enrollment_service is None:
        try:
            enrollment_service = get_enrollment_service()
            identification_service = get_identification_service()
            db_manager = get_database_manager()
        except Exception as e:
            logger.warning(f"Services not yet initialized: {e}")
    return enrollment_service, identification_service, db_manager

telemetry_events: List[Dict[str, Any]] = []


# ============================================
# Include Modular Routes
# ============================================
# Temporarily disable modular routes to avoid conflicts
# Enable modular route architecture
# try:
#     from .routes import enroll, identify, people, auth, health
#     
#     app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
#     app.include_router(enroll.router, prefix="/api/v1", tags=["enrollment"])
#     app.include_router(identify.router, prefix="/api/v1", tags=["identification"])
#     app.include_router(people.router, prefix="/api/v1", tags=["people"])
#     app.include_router(health.router, tags=["health"])
#     
#     logger.info("✅ Modular routes enabled: auth, enroll, identify, people, health")
# except ImportError as e:
#     logger.warning(f"⚠️ Could not import modular routes: {e}")
logger.info("ℹ️ Using inline routes defined in app.py")


# ============================================
# Pydantic Models
# ============================================


class EnrollmentRequest(BaseModel):
    user_name: str
    gender: Optional[str] = ""
    birth_year: Optional[str] = ""
    hometown: Optional[str] = ""
    residence: Optional[str] = ""

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_name": "John Doe",
                "gender": "Male",
                "birth_year": "1990",
                "hometown": "New York, USA",
                "residence": "London, UK",
            }
        }
    }


# IdentificationResponse is now imported from api.schemas


class DeletePersonResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Successfully deleted person 'person_abcdef123456'",
            }
        }
    }


# PersonInfo model - used for /api/v1/people endpoints
# Note: This is kept separate from schemas.PersonResponse for backward compatibility
class PersonInfo(BaseModel):
    folder_name: str
    user_name: str
    gender: Optional[str]
    birth_year: Optional[str]
    hometown: Optional[str]
    residence: Optional[str]
    embedding_count: int
    created_at: str
    updated_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "folder_name": "person_abcdef123456",
                "user_name": "Jane Doe",
                "gender": "Female",
                "birth_year": "1992",
                "hometown": "Los Angeles, USA",
                "residence": "San Francisco, USA",
                "embedding_count": 3,
                "created_at": "2023-10-27T10:00:00Z",
                "updated_at": "2023-10-27T12:30:00Z",
            }
        }
    }


class TelemetryEvent(BaseModel):
    client_id: Optional[str] = None
    transport: str = "rest"
    latency_ms: Optional[float] = None
    status: str = "unknown"
    faces_detected: Optional[int] = 0
    error_message: Optional[str] = None
    timestamp: Optional[str] = None
    api_endpoint: Optional[str] = None
    interval_seconds: Optional[float] = None


class TelemetryResponse(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "cpu_usage": 15.5,
                "memory_usage": 45.8,
                "disk_usage": 75.2,
            }
        }
    }


# EnrollmentResponse is now imported from api.schemas


# ============================================
# Health Checks
# ============================================


@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check - verify all services are ready"""
    try:
        if db_manager is None:
            return {"status": "degraded", "database": "unavailable"}

        # Perform a lightweight health check
        db_health = db_manager.check_health()

        if db_health["status"] != "ok":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database not ready: {db_health.get('error', 'Unknown error')}",
            )

        return {
            "status": "ready",
            "database": db_health,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not ready"
        )


# ============================================
# Enrollment Endpoints
# ============================================

def get_enrollment_data(
    user_name: str = Form(...),
    gender: Optional[str] = Form(""),
    birth_year: Optional[str] = Form(""),
    hometown: Optional[str] = Form(""),
    residence: Optional[str] = Form(""),
) -> EnrollmentRequest:
    return EnrollmentRequest(
        user_name=user_name,
        gender=gender,
        birth_year=birth_year,
        hometown=hometown,
        residence=residence,
    )



@app.post("/api/v1/enroll", response_model=EnrollmentResponse)
async def enroll_face(
    image: UploadFile = File(...),
    enrollment_data: EnrollmentRequest = Depends(get_enrollment_data),
) -> EnrollmentResponse:
    """
    Enroll a new face into the system. No authentication required.

    - **image**: Face image file (JPG, PNG)
    - **enrollment_data**: Person's metadata as a JSON object
    """
    start_time = datetime.now()
    
    try:
        # Check if enrollment service is initialized
        if enrollment_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="⚠️ AWS services not configured. Please set AWS_S3_BUCKET, AWS_REKOGNITION_COLLECTION, and AWS_DYNAMODB tables in .env file."
            )
        
        image_bytes = await image.read()

        # Enroll face
        result = enrollment_service.enroll_face(
            image_bytes=image_bytes, **enrollment_data.model_dump()
        )
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        success = result["success"]
        if success:
            logger.info(f"Enrollment successful: {enrollment_data.user_name}")
            return EnrollmentResponse(**result, processing_time_ms=processing_time)
        else:
            logger.warning(f"Enrollment failed: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Enrollment error: {error_msg}")
        # Return 400 for expected errors (AWS config), 500 for unexpected
        if "AWS" in error_msg or "bucket" in error_msg.lower() or "configuration" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"⚠️ AWS services not configured. This feature requires AWS setup. Error: {error_msg}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


# ============================================
# Identification Endpoints
# ============================================


@app.post("/api/v1/identify", response_model=IdentificationResponse)
async def identify_face(
    image: UploadFile = File(...),
    threshold: float = 0.6,
):
    """
    Identify faces in an image. No authentication required.

    - **image**: Image file containing face(s)
    - **threshold**: Recognition threshold (0.0-1.0, lower = more strict)
    """

    start_time = datetime.now()
    try:
        # Check if identification service is initialized
        if identification_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="⚠️ AWS services not configured. Please set AWS_REKOGNITION_COLLECTION and AWS_DYNAMODB tables in .env file."
            )
        
        image_bytes = await image.read()

        # Convert threshold from 0-1 to 0-100 for Rekognition
        rekognition_threshold = threshold * 100

        result = identification_service.identify_face(
            image_bytes=image_bytes, confidence_threshold=rekognition_threshold
        )
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"Identification: {result['faces_detected']} faces detected")

        return IdentificationResponse(
            success=result["success"],
            faces_detected=result["faces_detected"],
            processing_time_ms=processing_time,
            faces=result["faces"],
        )

    except Exception as e:
        logger.error(f"Identification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ============================================
# Telemetry Endpoint
# ============================================


@app.get("/api/v1/telemetry", response_model=TelemetryResponse)
async def get_telemetry() -> TelemetryResponse:
    """
    Get real-time system performance metrics. No authentication required.
    """
    cpu_usage = psutil.cpu_percent(interval=0.1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage("/")

    return TelemetryResponse(
        cpu_usage=cpu_usage,
        memory_usage=memory_info.percent,
        disk_usage=disk_info.percent,
    )


# ============================================
# Database Management Endpoints
# ============================================


@app.get("/api/v1/people")
def list_people():
    """Get list of all enrolled people. No authentication required."""
    # Simplified version - return empty list for now
    # Desktop app will show "No people enrolled yet"
    logger.info("GET /api/v1/people - Returning empty list (AWS not configured)")
    return []

@app.get("/api/v1/test")
def test_endpoint():
    """Simple test endpoint."""
    return {"status": "ok", "message": "API is working"}


@app.get("/api/v1/people/{folder_name}", response_model=PersonInfo)
async def get_person(folder_name: str):
    """Get detailed information about a person. No authentication required."""
    
    try:
        if db_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service not available",
            )
        person = db_manager.get_person(folder_name)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person '{folder_name}' not found",
            )
        # Map person_id to folder_name for compatibility
        if 'person_id' in person and 'folder_name' not in person:
            person['folder_name'] = person['person_id']
        # Convert Decimal to int/float for JSON serialization
        if 'embedding_count' in person and not isinstance(person['embedding_count'], (int, float)):
            person['embedding_count'] = int(person['embedding_count'])
        return person
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting person: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.delete("/api/v1/people/{folder_name}", response_model=DeletePersonResponse)
async def delete_person(folder_name: str) -> DeletePersonResponse:
    """Delete a person from the database. No authentication required."""
    
    try:
        result = db_manager.delete_person(folder_name)
        if result["success"]:
            logger.info(f"Deleted person: {folder_name}")
            return DeletePersonResponse(
                success=True,
                message=f"Successfully deleted person '{folder_name}'"
            )
        else:
            error_msg = result.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Failed to delete person: {error_msg}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting person: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )





@app.post("/api/v1/telemetry")
async def ingest_telemetry(event: TelemetryEvent):
    """Receive telemetry events (local testing)."""
    payload = event.model_dump()
    payload["received_at"] = datetime.now(timezone.utc).isoformat()
    telemetry_events.append(payload)
    if len(telemetry_events) > 1000:
        telemetry_events.pop(0)
    logger.info("Telemetry event: %s", payload)
    return {"status": "accepted"}


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import os

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "5555"))

    logger.info(f"Starting {settings.app_name} API Server")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"API URL: http://{host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
