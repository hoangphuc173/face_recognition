import os
from pydantic import BaseModel

class Settings(BaseModel):
    AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")
    COGNITO_USER_POOL_ID: str = os.environ.get("USER_POOL_ID", "")
    COGNITO_CLIENT_ID: str = os.environ.get("CLIENT_ID", "")
    DYNAMODB_TABLE_USERS: str = os.environ.get("USERS_TABLE", "Users")
    DYNAMODB_TABLE_ACCESS_LOGS: str = os.environ.get("ACCESS_LOGS_TABLE", "AccessLogs")
    S3_BUCKET_RAW: str = os.environ.get("RAW_BUCKET", "")
    S3_BUCKET_PROCESSED: str = os.environ.get("PROCESSED_BUCKET", "")
    REKOGNITION_COLLECTION_ID: str = os.environ.get("COLLECTION_ID", "FaceCollection")

settings = Settings()
