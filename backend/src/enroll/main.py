from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import boto3
import uuid
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from shared.config import settings
from shared.image_utils import preprocess_image, validate_image

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

s3 = boto3.client("s3", region_name=settings.AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
rekognition = boto3.client("rekognition", region_name=settings.AWS_REGION)

@app.post("/enroll")
async def enroll_user(
    file: UploadFile = File(None),
    image_base64: str = Form(None),
    name: str = Form(...),
    user_id: str = Form(None) # Optional, generate if not provided
):
    print(f"Enroll request - name: {name}, user_id: {user_id}")
    
    # Get image contents from either file or base64
    if image_base64:
        print(f"Received base64 image, length: {len(image_base64)}")
        import base64
        try:
            contents = base64.b64decode(image_base64)
        except Exception as e:
            print(f"Base64 decode error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid base64 data: {str(e)}")
    elif file:
        print(f"Received file: {file.filename}, content_type: {file.content_type}")
        contents = await file.read()
    else:
        raise HTTPException(status_code=400, detail="No image provided (neither file nor base64)")
    
    print(f"File size: {len(contents)} bytes")
    print(f"First 20 bytes: {contents[:20].hex()}")
    
    try:
        validate_image(contents)
    except ValueError as e:
        print(f"Invalid image validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    except Exception as e:
        print(f"Unexpected validation error: {e}")
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
    
    # Index Face - use Bytes directly instead of S3 to avoid region/permission issues
    try:
        response = rekognition.index_faces(
            CollectionId=settings.REKOGNITION_COLLECTION_ID,
            Image={'Bytes': processed_image},
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
    # CORS handled by middleware
    return result
