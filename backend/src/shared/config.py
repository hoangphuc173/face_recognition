import os
from pydantic import BaseModel

class Settings(BaseModel):
    AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")
    COGNITO_USER_POOL_ID: str = os.environ.get("COGNITO_USER_POOL_ID", "")
    COGNITO_CLIENT_ID: str = os.environ.get("COGNITO_CLIENT_ID", "")
    DYNAMODB_TABLE_USERS: str = os.environ.get("DYNAMODB_TABLE_USERS", "Users")
    DYNAMODB_TABLE_ACCESS_LOGS: str = os.environ.get("DYNAMODB_TABLE_ACCESS_LOGS", "AccessLogs")
    S3_BUCKET_RAW: str = os.environ.get("S3_BUCKET_RAW", "")
    S3_BUCKET_PROCESSED: str = os.environ.get("S3_BUCKET_PROCESSED", "")
    REKOGNITION_COLLECTION_ID: str = os.environ.get("REKOGNITION_COLLECTION_ID", "FaceCollection")

settings = Settings()
