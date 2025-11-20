"""
Reset Database Script - Xóa toàn bộ dữ liệu và tạo lại
- Xóa tất cả items trong DynamoDB tables (People, Embeddings, Matches)
- Xóa tất cả faces trong Rekognition collection
- Xóa tất cả files trong S3 bucket
"""

import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.aws.dynamodb_client import DynamoDBClient
from backend.aws.rekognition_client import RekognitionClient
from backend.aws.s3_client import S3Client
from backend.utils.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def clear_dynamodb_table(dynamodb_client, table_name):
    """Xóa tất cả items trong một bảng DynamoDB."""
    logger.info(f"🗑️  Đang xóa dữ liệu từ bảng: {table_name}")
    
    try:
        table = dynamodb_client.dynamodb.Table(table_name)
        
        # Scan toàn bộ bảng
        response = table.scan()
        items = response.get('Items', [])
        
        # Xóa từng item
        count = 0
        with table.batch_writer() as batch:
            for item in items:
                # Lấy key attributes (person_id, embedding_id, match_id)
                if 'person_id' in item and table_name.endswith('People'):
                    batch.delete_item(Key={'person_id': item['person_id']})
                    count += 1
                elif 'embedding_id' in item:
                    batch.delete_item(Key={'embedding_id': item['embedding_id']})
                    count += 1
                elif 'match_id' in item:
                    batch.delete_item(Key={'match_id': item['match_id']})
                    count += 1
        
        # Xử lý pagination nếu có nhiều items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items = response.get('Items', [])
            
            with table.batch_writer() as batch:
                for item in items:
                    if 'person_id' in item and table_name.endswith('People'):
                        batch.delete_item(Key={'person_id': item['person_id']})
                        count += 1
                    elif 'embedding_id' in item:
                        batch.delete_item(Key={'embedding_id': item['embedding_id']})
                        count += 1
                    elif 'match_id' in item:
                        batch.delete_item(Key={'match_id': item['match_id']})
                        count += 1
        
        logger.info(f"✅ Đã xóa {count} items từ {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi xóa {table_name}: {e}")
        return False


def clear_rekognition_collection(rekognition_client):
    """Xóa tất cả faces trong Rekognition collection."""
    logger.info("🗑️  Đang xóa faces từ Rekognition collection")
    
    if not rekognition_client.enabled or not rekognition_client.collection_id:
        logger.info("⚠️ Rekognition collection chưa được cấu hình, bỏ qua...")
        return True
    
    try:
        collection_id = rekognition_client.collection_id
        
        # List tất cả faces
        response = rekognition_client.client.list_faces(
            CollectionId=collection_id,
            MaxResults=1000
        )
        
        face_ids = [face['FaceId'] for face in response.get('Faces', [])]
        count = len(face_ids)
        
        # Xóa faces theo batch (tối đa 4096 faces mỗi lần)
        if face_ids:
            rekognition_client.client.delete_faces(
                CollectionId=collection_id,
                FaceIds=face_ids
            )
        
        # Xử lý pagination
        while 'NextToken' in response:
            response = rekognition_client.client.list_faces(
                CollectionId=collection_id,
                MaxResults=1000,
                NextToken=response['NextToken']
            )
            
            face_ids = [face['FaceId'] for face in response.get('Faces', [])]
            count += len(face_ids)
            
            if face_ids:
                rekognition_client.client.delete_faces(
                    CollectionId=collection_id,
                    FaceIds=face_ids
                )
        
        logger.info(f"✅ Đã xóa {count} faces từ Rekognition collection")
        return True
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi xóa Rekognition collection: {e}")
        return False


def clear_s3_bucket(s3_client, prefix="faces/"):
    """Xóa tất cả files trong S3 bucket với prefix nhất định."""
    logger.info(f"🗑️  Đang xóa files từ S3 bucket (prefix: {prefix})")
    
    if not s3_client.enabled or not s3_client.bucket_name:
        logger.info("⚠️ S3 chưa được cấu hình, bỏ qua...")
        return True
    
    try:
        bucket = s3_client.bucket_name
        
        # List tất cả objects
        response = s3_client.client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        objects = response.get('Contents', [])
        count = 0
        
        # Xóa objects theo batch
        if objects:
            delete_keys = [{'Key': obj['Key']} for obj in objects]
            s3_client.client.delete_objects(
                Bucket=bucket,
                Delete={'Objects': delete_keys}
            )
            count += len(delete_keys)
        
        # Xử lý pagination
        while response.get('IsTruncated', False):
            response = s3_client.client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                ContinuationToken=response['NextContinuationToken']
            )
            
            objects = response.get('Contents', [])
            if objects:
                delete_keys = [{'Key': obj['Key']} for obj in objects]
                s3_client.client.delete_objects(
                    Bucket=bucket,
                    Delete={'Objects': delete_keys}
                )
                count += len(delete_keys)
        
        logger.info(f"✅ Đã xóa {count} files từ S3 bucket")
        return True
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi xóa S3 bucket: {e}")
        return False


def main():
    """Main function để reset database."""
    logger.info("="*60)
    logger.info("🔄 BẮT ĐẦU RESET DATABASE")
    logger.info("="*60)
    
    # Load settings
    settings = get_settings()
    
    # Initialize clients
    logger.info("🔧 Khởi tạo AWS clients...")
    
    dynamodb_client = DynamoDBClient(
        region=settings.aws_region,
        people_table=settings.aws_dynamodb_people_table,
        embeddings_table=settings.aws_dynamodb_embeddings_table,
        matches_table=settings.aws_dynamodb_matches_table,
        enabled=True
    )
    
    rekognition_client = RekognitionClient(
        region=settings.aws_region,
        collection_id=settings.aws_rekognition_collection,
        enabled=True
    )
    
    s3_client = S3Client(
        region=settings.aws_region,
        bucket_name=settings.aws_s3_bucket,
        enabled=True
    )
    
    # Xác nhận
    print("\n⚠️  CẢNH BÁO: Hành động này sẽ xóa TOÀN BỘ dữ liệu!")
    print(f"   - DynamoDB Tables: {settings.aws_dynamodb_people_table}, {settings.aws_dynamodb_embeddings_table}, {settings.aws_dynamodb_matches_table}")
    print(f"   - Rekognition Collection: {settings.aws_rekognition_collection}")
    print(f"   - S3 Bucket: {settings.aws_s3_bucket}/faces/")
    
    confirm = input("\n❓ Bạn có chắc chắn muốn tiếp tục? (yes/no): ")
    
    if confirm.lower() != 'yes':
        logger.info("❌ Đã hủy reset database")
        return
    
    logger.info("\n" + "="*60)
    logger.info("🗑️  BẮT ĐẦU XÓA DỮ LIỆU")
    logger.info("="*60)
    
    # 1. Xóa DynamoDB tables
    logger.info("\n📊 Xóa DynamoDB Tables...")
    clear_dynamodb_table(dynamodb_client, settings.aws_dynamodb_people_table)
    clear_dynamodb_table(dynamodb_client, settings.aws_dynamodb_embeddings_table)
    clear_dynamodb_table(dynamodb_client, settings.aws_dynamodb_matches_table)
    
    # 2. Xóa Rekognition collection
    logger.info("\n👤 Xóa Rekognition Collection...")
    clear_rekognition_collection(rekognition_client)
    
    # 3. Xóa S3 bucket
    logger.info("\n📦 Xóa S3 Files...")
    clear_s3_bucket(s3_client)
    
    logger.info("\n" + "="*60)
    logger.info("✅ HOÀN THÀNH RESET DATABASE")
    logger.info("="*60)
    logger.info("📌 Database đã được làm sạch và sẵn sàng sử dụng!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n❌ Đã hủy bởi người dùng")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Lỗi: {e}", exc_info=True)
        sys.exit(1)
