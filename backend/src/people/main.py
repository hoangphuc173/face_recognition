from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import boto3
from boto3.dynamodb.conditions import Key
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from shared.config import settings

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",
    "https://master.d3d0ohwbet4zvk.amplifyapp.com",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
rekognition = boto3.client("rekognition", region_name=settings.AWS_REGION)
s3 = boto3.client("s3", region_name=settings.AWS_REGION)

@app.get("/people")
def list_people():
    table = dynamodb.Table(settings.DYNAMODB_TABLE_USERS)
    response = table.scan()
    items = response.get('Items', [])
    
    # Map DynamoDB keys to frontend expected keys
    mapped_items = []
    for item in items:
        mapped_items.append({
            "user_name": item.get("Name", ""),
            "person_id": item.get("UserId", ""),
            "face_id": item.get("FaceId", ""),
            "created_at": int(item.get("CreatedAt", 0)),
            "s3_key": item.get("S3Key", "")
        })
        
    return mapped_items

@app.put("/people/{user_id}")
def update_person(user_id: str, name: str = None):
    table = dynamodb.Table(settings.DYNAMODB_TABLE_USERS)
    
    # Check if user exists
    response = table.get_item(Key={'UserId': user_id})
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update name if provided
    if name:
        table.update_item(
            Key={'UserId': user_id},
            UpdateExpression='SET #name = :name',
            ExpressionAttributeNames={'#name': 'Name'},
            ExpressionAttributeValues={':name': name}
        )
    
    return {"message": "User updated", "UserId": user_id}

@app.delete("/people/{user_id}")
def delete_person(user_id: str):
    table = dynamodb.Table(settings.DYNAMODB_TABLE_USERS)
    
    # Get user to find FaceId and S3Key
    response = table.get_item(Key={'UserId': user_id})
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = response['Item']
    face_id = user.get('FaceId')
    s3_key = user.get('S3Key')
    
    # Delete from Rekognition
    if face_id:
        try:
            rekognition.delete_faces(
                CollectionId=settings.REKOGNITION_COLLECTION_ID,
                FaceIds=[face_id]
            )
        except Exception:
            pass # Ignore if already deleted
            
    # Delete from S3
    if s3_key:
        try:
            s3.delete_object(Bucket=settings.S3_BUCKET_PROCESSED, Key=s3_key)
        except Exception:
            pass
            
    # Delete from DynamoDB
    table.delete_item(Key={'UserId': user_id})
    
    return {"message": "User deleted"}

def handler(event, context):
    result = Mangum(app)(event, context)
    # CORS handled by middleware
    return result
