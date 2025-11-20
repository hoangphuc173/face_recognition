"""Shared dependencies for API routes.

This module provides singleton AWS clients and services
to avoid creating new connections on every request.
"""

import logging
from typing import Optional

from ..aws.s3_client import S3Client
from ..aws.rekognition_client import RekognitionClient
from ..aws.dynamodb_client import DynamoDBClient
from ..aws.redis_client import RedisClient
from ..core.enrollment_service import EnrollmentService
from ..core.identification_service import IdentificationService
from ..core.database_manager import DatabaseManager
from ..utils.config import settings

logger = logging.getLogger(__name__)

# Global shared instances (created once at startup)
_s3_client: Optional[S3Client] = None
_rekognition_client: Optional[RekognitionClient] = None
_dynamodb_client: Optional[DynamoDBClient] = None
_redis_client: Optional[RedisClient] = None
_enrollment_service: Optional[EnrollmentService] = None
_identification_service: Optional[IdentificationService] = None
_database_manager: Optional[DatabaseManager] = None


def initialize_clients():
    """Initialize all AWS clients and services at application startup."""
    global _s3_client, _rekognition_client, _dynamodb_client, _redis_client
    global _enrollment_service, _identification_service, _database_manager

    logger.info("🔧 Initializing shared AWS clients...")

    try:
        # Initialize AWS clients
        _s3_client = S3Client(
            bucket_name=settings.aws_s3_bucket,
            region=settings.aws_region
        )
        
        _rekognition_client = RekognitionClient(
            collection_id=settings.aws_rekognition_collection,
            region=settings.aws_region
        )
        
        _dynamodb_client = DynamoDBClient(
            region=settings.aws_region,
            people_table=settings.aws_dynamodb_people_table,
            embeddings_table=settings.aws_dynamodb_embeddings_table,
            matches_table=settings.aws_dynamodb_matches_table,
        )

        # Initialize Redis client (optional)
        if settings.redis_enabled:
            try:
                _redis_client = RedisClient(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password if settings.redis_password else None,
                    enabled=settings.redis_enabled,
                )
            except Exception as e:
                logger.warning(f"⚠️ Redis initialization failed: {e}")
                _redis_client = None

        # Initialize services with clients
        _enrollment_service = EnrollmentService(
            s3_client=_s3_client,
            rekognition_client=_rekognition_client,
            dynamodb_client=_dynamodb_client,
        )

        _identification_service = IdentificationService(
            rekognition_client=_rekognition_client,
            dynamodb_client=_dynamodb_client,
            s3_client=_s3_client,
            redis_client=_redis_client,
        )

        _database_manager = DatabaseManager(
            aws_dynamodb_client=_dynamodb_client,
            aws_s3_client=_s3_client,
        )

        logger.info("✅ Shared AWS clients initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize AWS clients: {e}")
        # Set to None to indicate failure
        _s3_client = None
        _rekognition_client = None
        _dynamodb_client = None
        _enrollment_service = None
        _identification_service = None
        _database_manager = None


def get_s3_client() -> S3Client:
    """Get shared S3 client instance."""
    if _s3_client is None:
        raise RuntimeError("S3 client not initialized. Call initialize_clients() first.")
    return _s3_client


def get_rekognition_client() -> RekognitionClient:
    """Get shared Rekognition client instance."""
    if _rekognition_client is None:
        raise RuntimeError("Rekognition client not initialized. Call initialize_clients() first.")
    return _rekognition_client


def get_dynamodb_client() -> DynamoDBClient:
    """Get shared DynamoDB client instance."""
    if _dynamodb_client is None:
        raise RuntimeError("DynamoDB client not initialized. Call initialize_clients() first.")
    return _dynamodb_client


def get_redis_client() -> Optional[RedisClient]:
    """Get shared Redis client instance (may be None if disabled)."""
    return _redis_client


def get_enrollment_service() -> EnrollmentService:
    """Get shared EnrollmentService instance."""
    if _enrollment_service is None:
        raise RuntimeError("EnrollmentService not initialized. Call initialize_clients() first.")
    return _enrollment_service


def get_identification_service() -> IdentificationService:
    """Get shared IdentificationService instance."""
    if _identification_service is None:
        raise RuntimeError("IdentificationService not initialized. Call initialize_clients() first.")
    return _identification_service


def get_database_manager() -> DatabaseManager:
    """Get shared DatabaseManager instance."""
    if _database_manager is None:
        raise RuntimeError("DatabaseManager not initialized. Call initialize_clients() first.")
    return _database_manager

