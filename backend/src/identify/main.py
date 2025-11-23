from fastapi import FastAPI, UploadFile, File, HTTPException
from mangum import Mangum
import boto3
import time
import uuid
from ..shared.config import settings
from ..shared.image_utils import preprocess_image, validate_image

app = FastAPI()

rekognition = boto3.client("rekognition", region_name=settings.AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)

@app.post("/identify")
async def identify_face(file: UploadFile = File(...)):
    contents = await file.read()
    
    if not validate_image(contents):
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
        # This is inefficient (N queries). Better to use BatchGetItem or cache.
        # For MVP, query is fine. Index on FaceId would be better.
        # Assuming FaceId is not the primary key (UserId is).
        # We need a GSI on FaceId in DynamoDB.
        
        # Scan is bad, but if we don't have GSI...
        # Let's assume we will create a GSI 'FaceIdIndex'
        
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
    if isinstance(result, dict):
        if 'headers' not in result:
            result['headers'] = {}
        result['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        })
    return result
