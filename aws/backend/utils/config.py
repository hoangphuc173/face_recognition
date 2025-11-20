"""Configuration management for Full-Stack Cloud AWS Architecture.

This module exposes a `Settings` Pydantic model with AWS-only configuration.
All face recognition operations use AWS Rekognition, S3, and DynamoDB.
"""

import os
from pathlib import Path
from typing import Any, Dict

# Load .env file explicitly
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from ..aws.secrets_manager_client import get_secret

try:
    from pydantic import BaseSettings, Field

    class Settings(BaseSettings):
        """Application settings for AWS Cloud-only deployment."""

        # App
        app_name: str = Field(default="Face Recognition System - Cloud", env="APP_NAME")
        app_env: str = Field(default="development", env="APP_ENV")
        debug: bool = Field(default=False, env="DEBUG")
        log_level: str = Field(default="INFO", env="LOG_LEVEL")

        # API
        api_host: str = Field(default="0.0.0.0", env="API_HOST")
        api_port: int = Field(default=8000, env="API_PORT")
        api_workers: int = Field(default=4, env="API_WORKERS")
        app_secrets_name: str = Field(default="face-recognition/secrets", env="APP_SECRETS_NAME")
        api_secret_key: str = Field(default="", env="API_SECRET_KEY")

        # Storage (AWS Only)
        max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")

        # Security
        enable_cors: bool = Field(default=True, env="ENABLE_CORS")
        jwt_secret_key: str = Field(default="", env="JWT_SECRET_KEY")
        jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
        jwt_expiration: int = Field(default=3600, env="JWT_EXPIRATION")
        api_key_enabled: bool = Field(default=False, env="API_KEY_ENABLED")
        api_key_header: str = Field(default="x-api-key", env="API_KEY_HEADER")
        api_key_value: str = Field(default="", env="API_KEY_VALUE")
        cognito_enabled: bool = Field(default=False, env="COGNITO_ENABLED")
        cognito_user_pool_id: str = Field(default="", env="COGNITO_USER_POOL_ID")
        cognito_region: str = Field(default="ap-southeast-1", env="COGNITO_REGION")
        cognito_app_client_id: str = Field(default="", env="COGNITO_APP_CLIENT_ID")

        # Monitoring
        enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
        metrics_port: int = Field(default=9090, env="METRICS_PORT")
        enable_xray: bool = Field(default=False, env="ENABLE_XRAY")

        # AWS Configuration (Required)
        aws_region: str = Field(default="ap-southeast-1", env="AWS_REGION")
        aws_account_id: str = Field(default="", env="AWS_ACCOUNT_ID")

        # AWS S3 (Required)
        aws_s3_bucket: str = Field(default="", env="AWS_S3_BUCKET")
        aws_s3_enrollment_prefix: str = Field(
            default="enrollments/", env="AWS_S3_ENROLLMENT_PREFIX"
        )
        aws_s3_identification_prefix: str = Field(
            default="identifications/", env="AWS_S3_IDENTIFICATION_PREFIX"
        )

        # AWS DynamoDB (Required)
        aws_dynamodb_people_table: str = Field(
            default="face-recognition-people-dev", env="AWS_DYNAMODB_PEOPLE_TABLE"
        )
        aws_dynamodb_embeddings_table: str = Field(
            default="face-recognition-embeddings-dev",
            env="AWS_DYNAMODB_EMBEDDINGS_TABLE",
        )
        aws_dynamodb_matches_table: str = Field(
            default="face-recognition-matches-dev", env="AWS_DYNAMODB_MATCHES_TABLE"
        )

        # AWS Rekognition (Required)
        aws_rekognition_collection: str = Field(
            default="", env="AWS_REKOGNITION_COLLECTION"
        )
        aws_rekognition_min_confidence: float = Field(
            default=80.0, env="AWS_REKOGNITION_MIN_CONFIDENCE"
        )
        aws_rekognition_max_faces: int = Field(
            default=5, env="AWS_REKOGNITION_MAX_FACES"
        )

        # AWS SQS (for async processing)
        aws_sqs_queue_url: str = Field(default="", env="AWS_SQS_QUEUE_URL")

        # AWS Lambda (for serverless deployment)
        lambda_timeout: int = Field(default=300, env="LAMBDA_TIMEOUT")
        lambda_memory: int = Field(default=512, env="LAMBDA_MEMORY")
        aws_lambda_identify_function_name: str = Field(
            default="", env="AWS_LAMBDA_IDENTIFY_FUNCTION_NAME"
        )

        # Redis Cache (NEW - for enhanced performance)
        redis_enabled: bool = Field(default=True, env="REDIS_ENABLED")
        redis_host: str = Field(default="localhost", env="REDIS_HOST")
        redis_port: int = Field(default=6379, env="REDIS_PORT")
        redis_db: int = Field(default=0, env="REDIS_DB")
        redis_password: str = Field(default="", env="REDIS_PASSWORD")
        redis_ttl_embedding: int = Field(default=3600, env="REDIS_TTL_EMBEDDING")  # 1 hour
        redis_ttl_user: int = Field(default=1800, env="REDIS_TTL_USER")  # 30 min
        redis_ttl_search: int = Field(default=300, env="REDIS_TTL_SEARCH")  # 5 min

        # Image Quality Validation (NEW - anti-spoofing)
        quality_check_enabled: bool = Field(default=True, env="QUALITY_CHECK_ENABLED")
        quality_min_brightness: float = Field(default=0.2, env="QUALITY_MIN_BRIGHTNESS")
        quality_max_brightness: float = Field(default=0.8, env="QUALITY_MAX_BRIGHTNESS")
        quality_min_contrast: float = Field(default=20.0, env="QUALITY_MIN_CONTRAST")
        quality_min_face_size: int = Field(default=100, env="QUALITY_MIN_FACE_SIZE")
        quality_max_head_pose: float = Field(default=30.0, env="QUALITY_MAX_HEAD_POSE")
        quality_min_images_enrollment: int = Field(default=5, env="QUALITY_MIN_IMAGES_ENROLLMENT")

        class Config:
            env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
            case_sensitive = True

except Exception:
    # Lightweight fallback when pydantic is not installed
    class Settings:
        def __init__(self) -> None:
            # App
            self.app_name = "Face Recognition System - Cloud"
            self.app_env = "development"
            self.debug = False
            self.log_level = "INFO"

            # API
            self.api_host = "0.0.0.0"
            self.api_port = 8000
            self.api_workers = 4
            self.api_secret_key = os.getenv("API_SECRET_KEY", "")

            # Storage
            self.max_file_size = 10485760

            # Security
            self.enable_cors = True
            self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
            self.jwt_algorithm = "HS256"
            self.jwt_expiration = 3600
            self.api_key_enabled = (
                os.getenv("API_KEY_ENABLED", "false").lower() == "true"
            )
            self.api_key_header = os.getenv("API_KEY_HEADER", "x-api-key")
            self.api_key_value = os.getenv("API_KEY_VALUE", "")
            self.cognito_enabled = (
                os.getenv("COGNITO_ENABLED", "false").lower() == "true"
            )
            self.cognito_user_pool_id = os.getenv("COGNITO_USER_POOL_ID", "")
            self.cognito_region = os.getenv("COGNITO_REGION", "ap-southeast-1")
            self.cognito_app_client_id = os.getenv("COGNITO_APP_CLIENT_ID", "")

            # Monitoring
            self.enable_metrics = True
            self.metrics_port = 9090
            self.enable_xray = os.getenv("ENABLE_XRAY", "false").lower() == "true"

            # Redis Cache
            self.redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
            self.redis_host = os.getenv("REDIS_HOST", "localhost")
            self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
            self.redis_db = int(os.getenv("REDIS_DB", "0"))
            self.redis_password = os.getenv("REDIS_PASSWORD", "")
            self.redis_ttl_embedding = int(os.getenv("REDIS_TTL_EMBEDDING", "3600"))
            self.redis_ttl_user = int(os.getenv("REDIS_TTL_USER", "1800"))
            self.redis_ttl_search = int(os.getenv("REDIS_TTL_SEARCH", "300"))

            # Image Quality Validation
            self.quality_check_enabled = os.getenv("QUALITY_CHECK_ENABLED", "true").lower() == "true"
            self.quality_min_brightness = float(os.getenv("QUALITY_MIN_BRIGHTNESS", "0.2"))
            self.quality_max_brightness = float(os.getenv("QUALITY_MAX_BRIGHTNESS", "0.8"))
            self.quality_min_contrast = float(os.getenv("QUALITY_MIN_CONTRAST", "20.0"))
            self.quality_min_face_size = int(os.getenv("QUALITY_MIN_FACE_SIZE", "100"))
            self.quality_max_head_pose = float(os.getenv("QUALITY_MAX_HEAD_POSE", "30.0"))
            self.quality_min_images_enrollment = int(os.getenv("QUALITY_MIN_IMAGES_ENROLLMENT", "5"))

            # AWS Configuration (Required)
            self.aws_region = os.getenv("AWS_REGION", "ap-southeast-1")
            self.aws_account_id = os.getenv("AWS_ACCOUNT_ID", "")

            # AWS S3
            self.aws_s3_bucket = os.getenv("AWS_S3_BUCKET", "")
            self.aws_s3_enrollment_prefix = os.getenv(
                "AWS_S3_ENROLLMENT_PREFIX", "enrollments/"
            )
            self.aws_s3_identification_prefix = os.getenv(
                "AWS_S3_IDENTIFICATION_PREFIX", "identifications/"
            )

            # AWS DynamoDB
            self.aws_dynamodb_people_table = os.getenv(
                "AWS_DYNAMODB_PEOPLE_TABLE", "face-recognition-people-dev"
            )
            self.aws_dynamodb_embeddings_table = os.getenv(
                "AWS_DYNAMODB_EMBEDDINGS_TABLE", "face-recognition-embeddings-dev"
            )
            self.aws_dynamodb_matches_table = os.getenv(
                "AWS_DYNAMODB_MATCHES_TABLE", "face-recognition-matches-dev"
            )

            # AWS Rekognition
            self.aws_rekognition_collection = os.getenv(
                "AWS_REKOGNITION_COLLECTION", ""
            )
            self.aws_rekognition_min_confidence = float(
                os.getenv("AWS_REKOGNITION_MIN_CONFIDENCE", "80.0")
            )
            self.aws_rekognition_max_faces = int(
                os.getenv("AWS_REKOGNITION_MAX_FACES", "5")
            )

            # AWS SQS
            self.aws_sqs_queue_url = os.getenv("AWS_SQS_QUEUE_URL", "")

            # AWS Lambda
            self.lambda_timeout = int(os.getenv("LAMBDA_TIMEOUT", "300"))
            self.lambda_memory = int(os.getenv("LAMBDA_MEMORY", "512"))
            self.aws_lambda_identify_function_name = os.getenv(
                "AWS_LAMBDA_IDENTIFY_FUNCTION_NAME", ""
            )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Return the global `settings` instance."""
    return settings
