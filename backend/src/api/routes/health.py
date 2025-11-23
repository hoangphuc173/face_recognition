"""
Health check routes.

NOTE: These routes are not currently integrated into app.py.
To use them, add: app.include_router(health.router, tags=["health"])
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ...core.database_manager import DatabaseManager
from ...aws.dynamodb_client import DynamoDBClient
from ...utils.config import Settings, get_settings
from ..schemas import HealthResponse

router = APIRouter()


def get_db_manager() -> DatabaseManager:
    """Dependency provider for DatabaseManager with DynamoDB."""
    settings = get_settings()
    dynamodb_client = DynamoDBClient(
        region=settings.aws_region,
        people_table=settings.aws_dynamodb_people_table,
        embeddings_table=settings.aws_dynamodb_embeddings_table,
        matches_table=settings.aws_dynamodb_matches_table,
    )
    return DatabaseManager(aws_dynamodb_client=dynamodb_client)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """Health check endpoint.

    Returns:
        Health status information
    """
    try:
        # Check database
        health_result = db_manager.check_health()
        if health_result.get("status") == "ok":
            db_status = "healthy"
        else:
            db_status = f"unhealthy: {health_result.get('error', 'Unknown error')}"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        environment=settings.app_env,
        database_status=db_status,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


@router.get("/ready")
async def readiness_check(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Readiness check endpoint for Kubernetes.

    Returns:
        Readiness status
    """
    try:
        # Quick check - can we access the database?
        health_result = db_manager.check_health()
        if health_result.get("status") == "ok":
            return JSONResponse({"status": "ready"})
        else:
            return JSONResponse(
                {"status": "not ready", "error": health_result.get("error", "Unknown error")},
                status_code=503
            )
    except Exception as e:
        return JSONResponse({"status": "not ready", "error": str(e)}, status_code=503)


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint for Kubernetes.

    Returns:
        Liveness status
    """
    return JSONResponse({"status": "alive"})
