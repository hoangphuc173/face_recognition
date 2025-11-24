from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import boto3
import time
import uuid
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

rekognition = boto3.client("rekognition", region_name=settings.AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)

@app.post("/identify")
async def identify_face(
    file: UploadFile = File(None),
    image_base64: str = Form(None)
):
    # Get image contents from either file or base64
    if image_base64:
        import base64
        try:
            contents = base64.b64decode(image_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 data: {str(e)}")
    elif file:
        contents = await file.read()
    else:
        raise HTTPException(status_code=400, detail="No image provided")
    
    try:
        validate_image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")
        
    processed_image = preprocess_image(contents)
    
    try:
        response = rekognition.search_faces_by_image(
            CollectionId=settings.REKOGNITION_COLLECTION_ID,
            Image={'Bytes': processed_image},
            FaceMatchThreshold=90,
            MaxFaces=5
        )
    except Exception as e:
        # If collection doesn't exist or other error
        print(f"Rekognition error: {e}")
        return {"matches": []}
        
    matches = []
    users_table = dynamodb.Table(settings.DYNAMODB_TABLE_USERS)
    logs_table = dynamodb.Table(settings.DYNAMODB_TABLE_ACCESS_LOGS)
    
    timestamp = int(time.time())
    
    for match in response['FaceMatches']:
        face_id = match['Face']['FaceId']
        confidence = match['Similarity']
        
        # Get User Info from DynamoDB
        user_info = None
        try:
            # Query using GSI
            result = users_table.query(
                IndexName='FaceIdIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('FaceId').eq(face_id)
            )
            if result['Items']:
                user_info = result['Items'][0]
        except Exception as e:
            print(f"DB Error: {e}")
            
        user_data = {
            "user_id": user_info['UserId'] if user_info else "Unknown",
            "name": user_info['Name'] if user_info else "Unknown",
            "confidence": confidence,
            "face_id": face_id,
            "bbox": match['Face']['BoundingBox']
        }
        matches.append(user_data)
        
        # Log access
        logs_table.put_item(
            Item={
                'LogId': str(uuid.uuid4()),
                'Timestamp': timestamp,
                'UserId': user_data['user_id'],
                'Confidence': str(confidence),
                'Action': 'IDENTIFY'
            }
        )
        
    return {"matches": matches}

def handler(event, context):
    result = Mangum(app)(event, context)
    # CORS handled by middleware
    return result
