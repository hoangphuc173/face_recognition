"""
Batch Enrollment Processor
Xử lý batch enrollment từ SQS queue với Kinesis streaming (theo báo cáo phần 5.4)
"""

import os
import json
import boto3
import logging
from typing import Dict, Any, List
from datetime import datetime

# Khởi tạo AWS clients
sqs = boto3.client('sqs')
kinesis = boto3.client('kinesis')
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')

# Cấu hình từ environment
QUEUE_URL = os.environ['ENROLLMENT_QUEUE_URL']
KINESIS_STREAM = os.environ.get('KINESIS_STREAM_NAME', 'face-enrollment-stream')
COLLECTION_ID = os.environ['AWS_REKOGNITION_COLLECTION']
EMBEDDINGS_TABLE = os.environ['DYNAMODB_EMBEDDINGS_TABLE']
USERS_TABLE = os.environ['DYNAMODB_USERS_TABLE']
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '10'))

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main handler cho batch enrollment processing
    - Đọc từ SQS queue
    - Stream events qua Kinesis
    - Index faces vào Rekognition collection
    - Cập nhật DynamoDB
    """
    
    try:
        # Nhận messages từ SQS
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=BATCH_SIZE,
            WaitTimeSeconds=5,
            MessageAttributeNames=['All']
        )
        
        messages = response.get('Messages', [])
        if not messages:
            logger.info("No messages in queue")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No messages to process'})
            }
        
        logger.info(f"Processing {len(messages)} enrollment requests")
        
        processed_count = 0
        failed_count = 0
        
        for message in messages:
            try:
                # Parse message body
                body = json.loads(message['Body'])
                user_id = body['user_id']
                image_s3_keys = body['image_s3_keys']
                metadata = body.get('metadata', {})
                
                # Stream enrollment event qua Kinesis
                kinesis_record = {
                    'user_id': user_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'event_type': 'enrollment_start',
                    'image_count': len(image_s3_keys)
                }
                
                kinesis.put_record(
                    StreamName=KINESIS_STREAM,
                    Data=json.dumps(kinesis_record),
                    PartitionKey=user_id
                )
                
                # Process từng ảnh
                face_ids = []
                for s3_key in image_s3_keys:
                    try:
                        # Index face với Rekognition
                        rekognition_response = rekognition.index_faces(
                            CollectionId=COLLECTION_ID,
                            Image={
                                'S3Object': {
                                    'Bucket': os.environ['S3_BUCKET'],
                                    'Name': s3_key
                                }
                            },
                            ExternalImageId=f"{user_id}_{datetime.utcnow().timestamp()}",
                            DetectionAttributes=['ALL'],
                            MaxFaces=1,
                            QualityFilter='AUTO'
                        )
                        
                        # Lưu face IDs
                        for face_record in rekognition_response.get('FaceRecords', []):
                            face_id = face_record['Face']['FaceId']
                            face_ids.append(face_id)
                            
                            # Lưu embedding vào DynamoDB
                            embeddings_table = dynamodb.Table(EMBEDDINGS_TABLE)
                            embeddings_table.put_item(Item={
                                'embedding_id': face_id,
                                'user_id': user_id,
                                'source_image_s3_path': s3_key,
                                'quality_score': face_record['Face'].get('Confidence', 0),
                                'model_version': 'rekognition-v5',
                                'created_at': datetime.utcnow().isoformat(),
                                'bounding_box': json.dumps(face_record['Face']['BoundingBox']),
                                'landmarks': json.dumps(face_record['FaceDetail'].get('Landmarks', []))
                            })
                            
                            logger.info(f"Indexed face {face_id} for user {user_id}")
                    
                    except rekognition.exceptions.InvalidParameterException as e:
                        logger.error(f"Invalid image {s3_key}: {str(e)}")
                        continue
                
                # Cập nhật user record
                if face_ids:
                    users_table = dynamodb.Table(USERS_TABLE)
                    users_table.update_item(
                        Key={'user_id': user_id},
                        UpdateExpression='SET embedding_count = :count, updated_at = :updated, #status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={
                            ':count': len(face_ids),
                            ':updated': datetime.utcnow().isoformat(),
                            ':status': 'active'
                        }
                    )
                    
                    # Stream success event
                    success_event = {
                        'user_id': user_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'event_type': 'enrollment_complete',
                        'face_ids': face_ids,
                        'status': 'success'
                    }
                    
                    kinesis.put_record(
                        StreamName=KINESIS_STREAM,
                        Data=json.dumps(success_event),
                        PartitionKey=user_id
                    )
                    
                    processed_count += 1
                
                # Xóa message khỏi queue
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=message['ReceiptHandle']
                )
                
            except Exception as e:
                logger.error(f"Failed to process message: {str(e)}")
                failed_count += 1
                
                # Stream failure event
                failure_event = {
                    'user_id': body.get('user_id', 'unknown'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'event_type': 'enrollment_failed',
                    'error': str(e),
                    'status': 'failed'
                }
                
                try:
                    kinesis.put_record(
                        StreamName=KINESIS_STREAM,
                        Data=json.dumps(failure_event),
                        PartitionKey=body.get('user_id', 'unknown')
                    )
                except Exception as ke:
                    logger.error(f"Failed to stream error event: {str(ke)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': processed_count,
                'failed': failed_count,
                'total': len(messages)
            })
        }
    
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def process_kinesis_events(event, context):
    """
    Handler riêng để xử lý Kinesis stream events
    Dùng cho analytics, monitoring, audit
    """
    
    logger.info(f"Processing {len(event['Records'])} Kinesis records")
    
    for record in event['Records']:
        try:
            # Decode Kinesis data
            payload = json.loads(record['kinesis']['data'])
            
            event_type = payload.get('event_type')
            user_id = payload.get('user_id')
            timestamp = payload.get('timestamp')
            
            logger.info(f"Event: {event_type} for user {user_id} at {timestamp}")
            
            # Có thể thêm logic xử lý event:
            # - Gửi SNS notification
            # - Cập nhật analytics dashboard
            # - Lưu audit trail
            # - Trigger downstream workflows
            
        except Exception as e:
            logger.error(f"Failed to process Kinesis record: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Kinesis events processed'})
    }
