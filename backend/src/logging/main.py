from fastapi import FastAPI, HTTPException
from mangum import Mangum
import boto3
from ..shared.config import settings

app = FastAPI()

dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)

@app.get("/logs")
def get_logs(limit: int = 50):
    table = dynamodb.Table(settings.DYNAMODB_TABLE_ACCESS_LOGS)
    # Scan is not efficient for logs, but for MVP it's okay.
    # Ideally query by timestamp index.
    response = table.scan(Limit=limit)
    items = response.get('Items', [])
    # Sort by timestamp desc
    items.sort(key=lambda x: x.get('Timestamp', 0), reverse=True)
    return items

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
