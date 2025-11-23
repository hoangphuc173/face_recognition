"""
Create Database Script - Tạo các bảng DynamoDB và Rekognition collection
- Tạo bảng People table
- Tạo bảng Embeddings table
- Tạo bảng Matches table (optional)
- Tạo Rekognition collection (nếu cấu hình)
"""

import logging
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.utils.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_people_table(dynamodb, table_name, region):
    """Tạo bảng People table trong DynamoDB."""
    logger.info(f"📊 Đang tạo bảng: {table_name}")
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'person_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'person_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',  # On-demand pricing
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'FaceRecognition'
                },
                {
                    'Key': 'Environment',
                    'Value': 'Development'
                }
            ]
        )
        
        # Wait until table exists
        logger.info(f"⏳ Đợi bảng {table_name} được tạo...")
        table.wait_until_exists()
        
        logger.info(f"✅ Đã tạo thành công bảng: {table_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info(f"ℹ️  Bảng {table_name} đã tồn tại")
            return True
        else:
            logger.error(f"❌ Lỗi khi tạo bảng {table_name}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Lỗi không mong đợi khi tạo {table_name}: {e}")
        return False


def create_embeddings_table(dynamodb, table_name, region):
    """Tạo bảng Embeddings table trong DynamoDB."""
    logger.info(f"📊 Đang tạo bảng: {table_name}")
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'embedding_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'embedding_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'person_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'person_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'person_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'FaceRecognition'
                },
                {
                    'Key': 'Environment',
                    'Value': 'Development'
                }
            ]
        )
        
        # Wait until table exists
        logger.info(f"⏳ Đợi bảng {table_name} được tạo...")
        table.wait_until_exists()
        
        logger.info(f"✅ Đã tạo thành công bảng: {table_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info(f"ℹ️  Bảng {table_name} đã tồn tại")
            return True
        else:
            logger.error(f"❌ Lỗi khi tạo bảng {table_name}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Lỗi không mong đợi khi tạo {table_name}: {e}")
        return False


def create_matches_table(dynamodb, table_name, region):
    """Tạo bảng Matches table trong DynamoDB (optional)."""
    logger.info(f"📊 Đang tạo bảng: {table_name}")
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'match_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'match_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'person_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'person_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'person_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'FaceRecognition'
                },
                {
                    'Key': 'Environment',
                    'Value': 'Development'
                }
            ]
        )
        
        # Wait until table exists
        logger.info(f"⏳ Đợi bảng {table_name} được tạo...")
        table.wait_until_exists()
        
        logger.info(f"✅ Đã tạo thành công bảng: {table_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info(f"ℹ️  Bảng {table_name} đã tồn tại")
            return True
        else:
            logger.error(f"❌ Lỗi khi tạo bảng {table_name}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Lỗi không mong đợi khi tạo {table_name}: {e}")
        return False


def create_rekognition_collection(rekognition_client, collection_id):
    """Tạo Rekognition collection."""
    if not collection_id:
        logger.info("⚠️  Rekognition collection ID không được cấu hình, bỏ qua...")
        return True
    
    logger.info(f"👤 Đang tạo Rekognition collection: {collection_id}")
    
    try:
        rekognition_client.create_collection(CollectionId=collection_id)
        logger.info(f"✅ Đã tạo thành công collection: {collection_id}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            logger.info(f"ℹ️  Collection {collection_id} đã tồn tại")
            return True
        else:
            logger.error(f"❌ Lỗi khi tạo collection {collection_id}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Lỗi không mong đợi khi tạo collection: {e}")
        return False


def create_s3_bucket(s3_client, bucket_name, region):
    """Tạo S3 bucket (nếu cần)."""
    if not bucket_name:
        logger.info("⚠️  S3 bucket name không được cấu hình, bỏ qua...")
        return True
    
    logger.info(f"📦 Đang tạo S3 bucket: {bucket_name}")
    
    try:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        # Enable versioning
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # Block public access
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        
        logger.info(f"✅ Đã tạo thành công bucket: {bucket_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            logger.info(f"ℹ️  Bucket {bucket_name} đã tồn tại")
            return True
        elif e.response['Error']['Code'] == 'BucketAlreadyExists':
            logger.warning(f"⚠️  Bucket {bucket_name} đã tồn tại (thuộc account khác)")
            return False
        else:
            logger.error(f"❌ Lỗi khi tạo bucket {bucket_name}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Lỗi không mong đợi khi tạo bucket: {e}")
        return False


def main():
    """Main function để tạo database."""
    logger.info("="*60)
    logger.info("🚀 BẮT ĐẦU TẠO DATABASE")
    logger.info("="*60)
    
    # Load settings
    settings = get_settings()
    
    logger.info(f"\n📋 Thông tin cấu hình:")
    logger.info(f"   - AWS Region: {settings.aws_region}")
    logger.info(f"   - People Table: {settings.aws_dynamodb_people_table}")
    logger.info(f"   - Embeddings Table: {settings.aws_dynamodb_embeddings_table}")
    logger.info(f"   - Matches Table: {settings.aws_dynamodb_matches_table}")
    logger.info(f"   - Rekognition Collection: {settings.aws_rekognition_collection or '(chưa cấu hình)'}")
    logger.info(f"   - S3 Bucket: {settings.aws_s3_bucket or '(chưa cấu hình)'}")
    
    # Initialize AWS clients
    logger.info(f"\n🔧 Khởi tạo AWS clients...")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        rekognition = boto3.client('rekognition', region_name=settings.aws_region)
        s3 = boto3.client('s3', region_name=settings.aws_region)
        
        logger.info("✅ AWS clients đã được khởi tạo")
    except Exception as e:
        logger.error(f"❌ Không thể khởi tạo AWS clients: {e}")
        logger.error("💡 Vui lòng kiểm tra AWS credentials (aws configure)")
        return False
    
    logger.info("\n" + "="*60)
    logger.info("📊 TẠO DYNAMODB TABLES")
    logger.info("="*60)
    
    success = True
    
    # 1. Tạo People table
    if not create_people_table(dynamodb, settings.aws_dynamodb_people_table, settings.aws_region):
        success = False
    
    # 2. Tạo Embeddings table
    if not create_embeddings_table(dynamodb, settings.aws_dynamodb_embeddings_table, settings.aws_region):
        success = False
    
    # 3. Tạo Matches table (optional)
    if not create_matches_table(dynamodb, settings.aws_dynamodb_matches_table, settings.aws_region):
        success = False
    
    # 4. Tạo Rekognition collection
    logger.info("\n" + "="*60)
    logger.info("👤 TẠO REKOGNITION COLLECTION")
    logger.info("="*60)
    
    if not create_rekognition_collection(rekognition, settings.aws_rekognition_collection):
        success = False
    
    # 5. Tạo S3 bucket (optional)
    logger.info("\n" + "="*60)
    logger.info("📦 TẠO S3 BUCKET")
    logger.info("="*60)
    
    if not create_s3_bucket(s3, settings.aws_s3_bucket, settings.aws_region):
        logger.warning("⚠️  Không thể tạo S3 bucket, nhưng có thể bucket đã tồn tại")
    
    # Summary
    logger.info("\n" + "="*60)
    if success:
        logger.info("✅ HOÀN THÀNH TẠO DATABASE")
        logger.info("="*60)
        logger.info("📌 Database đã sẵn sàng sử dụng!")
        logger.info("\n💡 Các bước tiếp theo:")
        logger.info("   1. Kiểm tra các bảng trong AWS Console")
        logger.info("   2. Khởi động API server: python -m uvicorn backend.api.app:app --reload")
        logger.info("   3. Test API endpoints")
        return True
    else:
        logger.error("❌ CÓ LỖI XẢY RA KHI TẠO DATABASE")
        logger.info("="*60)
        logger.error("💡 Vui lòng kiểm tra logs ở trên và sửa lỗi")
        return False


if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\n❌ Đã hủy bởi người dùng")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Lỗi: {e}", exc_info=True)
        sys.exit(1)
