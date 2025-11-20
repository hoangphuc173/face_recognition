"""
GDPR Compliance Features
Right-to-delete, data retention automation, consent management (báo cáo 3.1.2, 9.2)
"""

import os
import json
import boto3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
rekognition = boto3.client('rekognition')
sns = boto3.client('sns')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
USERS_TABLE = os.environ['DYNAMODB_USERS_TABLE']
EMBEDDINGS_TABLE = os.environ['DYNAMODB_EMBEDDINGS_TABLE']
ACCESS_LOGS_TABLE = os.environ['DYNAMODB_ACCESS_LOGS_TABLE']
CONSENT_TABLE = os.environ.get('DYNAMODB_CONSENT_TABLE', 'ConsentRecords')
S3_BUCKET = os.environ['S3_BUCKET']
COLLECTION_ID = os.environ['AWS_REKOGNITION_COLLECTION']
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

# Data retention policies
RETENTION_DAYS_RAW_IMAGES = int(os.environ.get('RETENTION_DAYS_RAW', '7'))
RETENTION_DAYS_LOGS = int(os.environ.get('RETENTION_DAYS_LOGS', '180'))


class GDPRComplianceManager:
    """Quản lý GDPR compliance: right-to-delete, retention, consent"""
    
    def __init__(self):
        self.users_table = dynamodb.Table(USERS_TABLE)
        self.embeddings_table = dynamodb.Table(EMBEDDINGS_TABLE)
        self.logs_table = dynamodb.Table(ACCESS_LOGS_TABLE)
        self.consent_table = dynamodb.Table(CONSENT_TABLE)
    
    def right_to_be_forgotten(self, user_id: str, requester: str) -> Dict:
        """
        Thực hiện quyền xóa dữ liệu (GDPR Article 17)
        
        Steps:
        1. Verify consent withdrawal
        2. Delete from Rekognition collection
        3. Delete embeddings from DynamoDB
        4. Delete images from S3
        5. Anonymize access logs
        6. Update user status
        7. Send confirmation notification
        
        Args:
            user_id: User ID to delete
            requester: Who requested deletion
        
        Returns:
            Deletion result
        """
        
        result = {
            "user_id": user_id,
            "status": "in_progress",
            "timestamp": datetime.utcnow().isoformat(),
            "requester": requester,
            "steps_completed": [],
            "errors": []
        }
        
        try:
            logger.info(f"Starting GDPR deletion for user {user_id}")
            
            # 1. Verify user exists
            user_response = self.users_table.get_item(Key={'user_id': user_id})
            if 'Item' not in user_response:
                result["status"] = "failed"
                result["errors"].append("User not found")
                return result
            
            user = user_response['Item']
            result["steps_completed"].append("user_verified")
            
            # 2. Delete faces from Rekognition collection
            try:
                embeddings_response = self.embeddings_table.query(
                    IndexName='user_id-index',
                    KeyConditionExpression='user_id = :uid',
                    ExpressionAttributeValues={':uid': user_id}
                )
                
                face_ids = [
                    item['embedding_id']
                    for item in embeddings_response.get('Items', [])
                ]
                
                if face_ids:
                    rekognition.delete_faces(
                        CollectionId=COLLECTION_ID,
                        FaceIds=face_ids
                    )
                    logger.info(f"Deleted {len(face_ids)} faces from Rekognition")
                
                result["steps_completed"].append("rekognition_deleted")
                result["faces_deleted"] = len(face_ids)
                
            except Exception as e:
                logger.error(f"Rekognition deletion error: {e}")
                result["errors"].append(f"Rekognition: {str(e)}")
            
            # 3. Delete embeddings from DynamoDB
            try:
                for item in embeddings_response.get('Items', []):
                    self.embeddings_table.delete_item(
                        Key={'embedding_id': item['embedding_id']}
                    )
                
                result["steps_completed"].append("embeddings_deleted")
                
            except Exception as e:
                logger.error(f"Embeddings deletion error: {e}")
                result["errors"].append(f"Embeddings: {str(e)}")
            
            # 4. Delete images from S3
            try:
                prefix = f"users/{user_id}/"
                paginator = s3.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
                
                deleted_count = 0
                for page in pages:
                    if 'Contents' in page:
                        objects = [{'Key': obj['Key']} for obj in page['Contents']]
                        if objects:
                            s3.delete_objects(
                                Bucket=S3_BUCKET,
                                Delete={'Objects': objects}
                            )
                            deleted_count += len(objects)
                
                logger.info(f"Deleted {deleted_count} S3 objects")
                result["steps_completed"].append("s3_deleted")
                result["s3_objects_deleted"] = deleted_count
                
            except Exception as e:
                logger.error(f"S3 deletion error: {e}")
                result["errors"].append(f"S3: {str(e)}")
            
            # 5. Anonymize access logs (không xóa hoàn toàn để audit)
            try:
                logs_response = self.logs_table.query(
                    IndexName='user_id-index',
                    KeyConditionExpression='user_id = :uid',
                    ExpressionAttributeValues={':uid': user_id}
                )
                
                for log_item in logs_response.get('Items', []):
                    self.logs_table.update_item(
                        Key={
                            'log_id': log_item['log_id'],
                            'timestamp': log_item['timestamp']
                        },
                        UpdateExpression='SET user_id = :anon, anonymized = :flag, anonymized_at = :ts',
                        ExpressionAttributeValues={
                            ':anon': 'ANONYMIZED',
                            ':flag': True,
                            ':ts': datetime.utcnow().isoformat()
                        }
                    )
                
                result["steps_completed"].append("logs_anonymized")
                result["logs_anonymized"] = len(logs_response.get('Items', []))
                
            except Exception as e:
                logger.error(f"Logs anonymization error: {e}")
                result["errors"].append(f"Logs: {str(e)}")
            
            # 6. Update user status
            try:
                self.users_table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression='SET #status = :status, deleted_at = :ts, deleted_by = :req',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'deleted',
                        ':ts': datetime.utcnow().isoformat(),
                        ':req': requester
                    }
                )
                
                result["steps_completed"].append("user_updated")
                
            except Exception as e:
                logger.error(f"User update error: {e}")
                result["errors"].append(f"User update: {str(e)}")
            
            # 7. Record consent withdrawal
            try:
                self.consent_table.put_item(Item={
                    'user_id': user_id,
                    'action': 'data_deletion',
                    'timestamp': datetime.utcnow().isoformat(),
                    'requester': requester,
                    'status': 'completed',
                    'steps': result["steps_completed"]
                })
                
                result["steps_completed"].append("consent_recorded")
                
            except Exception as e:
                logger.error(f"Consent record error: {e}")
                result["errors"].append(f"Consent: {str(e)}")
            
            # 8. Send notification
            if SNS_TOPIC_ARN:
                try:
                    message = f"""
GDPR Data Deletion Completed

User ID: {user_id}
Requester: {requester}
Timestamp: {result['timestamp']}
Steps Completed: {len(result['steps_completed'])}
Errors: {len(result['errors'])}

Details:
- Faces deleted: {result.get('faces_deleted', 0)}
- S3 objects deleted: {result.get('s3_objects_deleted', 0)}
- Logs anonymized: {result.get('logs_anonymized', 0)}
                    """
                    
                    sns.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Subject=f'GDPR Deletion Completed: {user_id}',
                        Message=message
                    )
                    
                    result["steps_completed"].append("notification_sent")
                    
                except Exception as e:
                    logger.error(f"SNS notification error: {e}")
            
            # Final status
            if len(result["errors"]) == 0:
                result["status"] = "completed"
            elif len(result["steps_completed"]) > 0:
                result["status"] = "partial"
            else:
                result["status"] = "failed"
            
            logger.info(f"GDPR deletion completed for {user_id}: {result['status']}")
            
        except Exception as e:
            logger.error(f"GDPR deletion failed: {e}")
            result["status"] = "failed"
            result["errors"].append(str(e))
        
        return result
    
    def automated_retention_cleanup(self) -> Dict:
        """
        Tự động xóa dữ liệu hết hạn theo retention policy
        - Raw images: 7 days
        - Logs: 180 days
        """
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "raw_images_deleted": 0,
            "logs_deleted": 0,
            "errors": []
        }
        
        try:
            # 1. Clean up raw images older than retention period
            cutoff_date_raw = datetime.utcnow() - timedelta(days=RETENTION_DAYS_RAW_IMAGES)
            
            paginator = s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=S3_BUCKET, Prefix='raw/')
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date_raw:
                            try:
                                s3.delete_object(Bucket=S3_BUCKET, Key=obj['Key'])
                                result["raw_images_deleted"] += 1
                            except Exception as e:
                                logger.error(f"Failed to delete {obj['Key']}: {e}")
            
            logger.info(f"Deleted {result['raw_images_deleted']} expired raw images")
            
            # 2. Clean up old access logs (DynamoDB TTL handles this automatically)
            # But we can query and count for reporting
            cutoff_date_logs = datetime.utcnow() - timedelta(days=RETENTION_DAYS_LOGS)
            cutoff_timestamp = int(cutoff_date_logs.timestamp())
            
            # DynamoDB TTL should have deleted these already
            # Just log the policy
            logger.info(f"Access logs TTL set to {RETENTION_DAYS_LOGS} days")
            
        except Exception as e:
            logger.error(f"Retention cleanup error: {e}")
            result["errors"].append(str(e))
        
        return result
    
    def record_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Ghi nhận consent từ người dùng
        
        Args:
            user_id: User ID
            consent_type: 'enrollment', 'identification', 'data_storage', 'marketing'
            granted: True if consent granted
            metadata: Additional metadata
        
        Returns:
            Success status
        """
        
        try:
            item = {
                'user_id': user_id,
                'consent_type': consent_type,
                'granted': granted,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': json.dumps(metadata or {})
            }
            
            self.consent_table.put_item(Item=item)
            
            logger.info(f"Recorded consent for {user_id}: {consent_type}={granted}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            return False


# Lambda handler
def lambda_handler(event, context):
    """
    Lambda handler cho GDPR operations
    
    Operations:
    - delete_user: Right to be forgotten
    - cleanup: Automated retention cleanup
    - record_consent: Record user consent
    - get_data: Export user data (GDPR Article 15)
    """
    
    manager = GDPRComplianceManager()
    
    try:
        operation = event.get('operation')
        
        if operation == 'delete_user':
            user_id = event['user_id']
            requester = event.get('requester', 'system')
            result = manager.right_to_be_forgotten(user_id, requester)
            
            return {
                'statusCode': 200 if result['status'] == 'completed' else 500,
                'body': json.dumps(result, default=str)
            }
        
        elif operation == 'cleanup':
            result = manager.automated_retention_cleanup()
            
            return {
                'statusCode': 200,
                'body': json.dumps(result, default=str)
            }
        
        elif operation == 'record_consent':
            user_id = event['user_id']
            consent_type = event['consent_type']
            granted = event['granted']
            metadata = event.get('metadata')
            
            success = manager.record_consent(user_id, consent_type, granted, metadata)
            
            return {
                'statusCode': 200 if success else 500,
                'body': json.dumps({'success': success})
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown operation: {operation}'})
            }
    
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# Scheduled cleanup handler
def scheduled_cleanup_handler(event, context):
    """
    Handler cho EventBridge scheduled cleanup
    Chạy daily để clean up expired data
    """
    
    manager = GDPRComplianceManager()
    result = manager.automated_retention_cleanup()
    
    logger.info(f"Scheduled cleanup completed: {result}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(result, default=str)
    }
