from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from mangum import Mangum
import boto3
import uuid
import time
from ..shared.config import settings
from ..shared.image_utils import preprocess_image, validate_image

app = FastAPI()

s3 = boto3.client("s3", region_name=settings.AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
rekognition = boto3.client("rekognition", region_name=settings.AWS_REGION)

@app.post("/enroll")
async def enroll_user(
    file: UploadFile = File(...),
    name: str = Form(...),
    user_id: str = Form(None) # Optional, generate if not provided
):
    contents = await file.read()
    
    if not validate_image(contents):
        raise HTTPException(status_code=400, detail="Invalid image file")
        
    processed_image = preprocess_image(contents)
    
    if not user_id:
        user_id = str(uuid.uuid4())
        
    # Upload to S3 (Raw and Processed)
    # Use user_id as folder
    key_raw = f"raw/{user_id}/{int(time.time())}.jpg"
    key_processed = f"processed/{user_id}/{int(time.time())}.jpg"
    
    s3.put_object(Bucket=settings.S3_BUCKET_RAW, Key=key_raw, Body=contents)
    s3.put_object(Bucket=settings.S3_BUCKET_PROCESSED, Key=key_processed, Body=processed_image)
    
    # Index Face
    try:
        response = rekognition.index_faces(
            CollectionId=settings.REKOGNITION_COLLECTION_ID,
            Image={'S3Object': {'Bucket': settings.S3_BUCKET_PROCESSED, 'Name': key_processed}},
            ExternalImageId=user_id,
            DetectionAttributes=['ALL']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rekognition error: {str(e)}")
        
    if not response['FaceRecords']:
        raise HTTPException(status_code=400, detail="No face detected")
        
    face_id = response['FaceRecords'][0]['Face']['FaceId']
    
    # Save to DynamoDB
    table = dynamodb.Table(settings.DYNAMODB_TABLE_USERS)
    table.put_item(
        Item={
            'UserId': user_id,
            'Name': name,
            'FaceId': face_id,
            'CreatedAt': int(time.time()),
            'S3Key': key_processed
        }
    )
    
    return {"user_id": user_id, "face_id": face_id, "name": name}

def handler(event, context):
    result = Mangum(app)(event, context)
    if isinstance(result, dict):
        if 'headers' not in result:
            result['headers'] = {}
        result['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        })
    return result
