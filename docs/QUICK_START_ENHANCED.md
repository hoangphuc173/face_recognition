# Quick Start Guide - Enhanced Features

## 🚀 Cài Đặt Dependencies Mới

```bash
# Cài đặt enhanced dependencies
pip install -r requirements-enhanced.txt

# Hoặc cài riêng lẻ
pip install redis hiredis opencv-python-headless numpy Pillow
```

## 🔧 Cấu Hình Redis Cache

### Option 1: Local Redis (Development)

```bash
# Install Redis locally
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# macOS: brew install redis

# Start Redis
redis-server
```

### Option 2: AWS ElastiCache (Production)

Sau khi deploy CDK stack, lấy Redis endpoint:

```bash
# Từ CDK outputs
export REDIS_HOST=face-recognition-cache-prod.abc123.0001.apse1.cache.amazonaws.com
export REDIS_PORT=6379
```

### Cập nhật `.env`

```bash
# aws/backend/.env
REDIS_HOST=localhost  # hoặc ElastiCache endpoint
REDIS_PORT=6379
REDIS_ENABLED=true
REDIS_TTL_EMBEDDING=3600  # 1 hour
REDIS_TTL_USER=1800       # 30 minutes
REDIS_TTL_SEARCH=300      # 5 minutes
```

## 📊 Sử Dụng Redis Cache

### Trong Code

```python
from aws.backend.aws.redis_client import RedisClient

# Initialize Redis client
redis_client = RedisClient(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    enabled=os.getenv("REDIS_ENABLED", "true").lower() == "true"
)

# Check health
health = redis_client.health_check()
print(f"Redis status: {health}")

# Use in IdentificationService
from aws.backend.core.identification_service import IdentificationService

service = IdentificationService(
    rekognition_client=rekognition,
    dynamodb_client=dynamodb,
    s3_client=s3,
    redis_client=redis_client  # NEW!
)

# identify_face tự động sử dụng cache
result = service.identify_face(image_bytes, use_cache=True)
print(f"Cache hit: {result['cache_hit']}")
```

## 🛡️ Image Quality Validation

### Sử Dụng Validator

```python
from aws.backend.utils.image_quality import ImageQualityValidator, get_validator

# Sử dụng validator mặc định
validator = get_validator()

# Hoặc custom thresholds
validator = ImageQualityValidator(
    min_brightness=0.2,
    max_brightness=0.8,
    min_contrast=20.0,
    min_face_size=100,
    max_head_pose=30.0
)

# Validate ảnh
with open("image.jpg", "rb") as f:
    image_bytes = f.read()

# Option 1: Chỉ kiểm tra ảnh (không cần face details)
result = validator.validate_image_quality(image_bytes)

# Option 2: Kiểm tra với face details từ Rekognition
from aws.backend.aws.rekognition_client import RekognitionClient

rekognition = RekognitionClient(collection_id="my-collection", region="ap-southeast-1")
detect_result = rekognition.detect_faces(image_bytes)

if detect_result["success"] and detect_result["faces"]:
    face_details = detect_result["faces"][0]
    result = validator.validate_image_quality(image_bytes, face_details)

# Xem kết quả
if result["valid"]:
    print("✅ Image quality OK")
else:
    print(f"⚠️ Quality issues: {result['warnings']}")
    print(f"Details: {result['checks']}")
```

### Enrollment với Quality Check

Quality validation đã được tích hợp tự động trong `EnrollmentService.enroll_face()`:

```python
from aws.backend.core.enrollment_service import EnrollmentService

service = EnrollmentService(s3_client, rekognition_client, dynamodb_client)

result = service.enroll_face(
    image_bytes=image_bytes,
    user_name="John Doe",
    check_duplicate=True
)

# Nếu ảnh kém chất lượng, enrollment sẽ bị reject
if not result["success"]:
    print(result["message"])
    if "quality_check" in result:
        print(f"Quality details: {result['quality_check']}")
```

## 🔄 Step Functions Workflows

### Deploy Workflows

```bash
cd aws/infrastructure/cdk
cdk deploy --all
```

### Invoke Identification Workflow

```bash
aws stepfunctions start-execution \
    --state-machine-arn arn:aws:states:ap-southeast-1:123456789012:stateMachine:face-recognition-identification-prod \
    --input '{
        "image": "base64_encoded_image_here",
        "threshold": 90.0
    }'
```

### Invoke Enrollment Workflow

```bash
aws stepfunctions start-execution \
    --state-machine-arn arn:aws:states:ap-southeast-1:123456789012:stateMachine:face-recognition-enrollment-prod \
    --input '{
        "image": "base64_encoded_image_here",
        "user_id": "user_123",
        "user_name": "John Doe"
    }'
```

### Monitor Execution

```bash
# Get execution ARN from previous command
aws stepfunctions describe-execution \
    --execution-arn arn:aws:states:...

# View execution history
aws stepfunctions get-execution-history \
    --execution-arn arn:aws:states:...
```

## 📈 CloudWatch Monitoring

### View Dashboard

```bash
# Get dashboard URL from CDK output
echo $DASHBOARD_URL

# Or construct manually
https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#dashboards:name=face-recognition-prod
```

### Query Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/face-recognition-identify-prod --follow

# Step Functions logs
aws logs tail /aws/stepfunctions/face-recognition-identification-prod --follow
```

### Custom Metrics

Trong Lambda code, publish custom metrics:

```python
import boto3
cloudwatch = boto3.client('cloudwatch')

# Publish recognition success
cloudwatch.put_metric_data(
    Namespace='face-recognition/Realtime',
    MetricData=[
        {
            'MetricName': 'RecognitionSuccess',
            'Value': 1.0 if success else 0.0,
            'Unit': 'None'
        },
        {
            'MetricName': 'RecognitionLatency',
            'Value': latency_ms,
            'Unit': 'Milliseconds'
        },
        {
            'MetricName': 'ConfidenceScore',
            'Value': confidence,
            'Unit': 'None'
        }
    ]
)
```

## 🧪 Testing

### Unit Tests

```bash
cd aws
pytest tests/core/test_identification_service.py -v
pytest tests/aws/test_redis_client.py -v
pytest tests/utils/test_image_quality.py -v
```

### Integration Tests

```bash
# Test với local Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
pytest tests/integration/ -v

# Test cache performance
python tests/benchmark_cache.py
```

### Load Testing

```bash
pip install locust

# Run load test
locust -f tests/load_test.py --host https://your-api-endpoint.com
```

## 🐛 Troubleshooting

### Redis Connection Issues

```python
# Check Redis health
from aws.backend.aws.redis_client import RedisClient

redis_client = RedisClient()
health = redis_client.health_check()
print(health)

# Output:
# {'enabled': True, 'connected': True, 'version': '7.0.0', ...}
```

### Image Quality Always Fails

```python
# Debug quality checks
from aws.backend.utils.image_quality import get_validator

validator = get_validator()
result = validator.validate_image_quality(image_bytes)

# Check individual checks
for check_name, check_data in result['checks'].items():
    print(f"{check_name}: {check_data}")

# Adjust thresholds if needed
validator.min_brightness = 0.1  # More permissive
validator.max_brightness = 0.9
```

### Cache Not Working

```bash
# Verify Redis is running
redis-cli ping
# Should return: PONG

# Check Redis keys
redis-cli keys "facerecog:*"

# Monitor Redis commands
redis-cli monitor
```

## 📚 Additional Resources

- [Redis Python Client Docs](https://redis-py.readthedocs.io/)
- [OpenCV Python Tutorial](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [AWS Step Functions](https://docs.aws.amazon.com/step-functions/)
- [CloudWatch Metrics](https://docs.aws.amazon.com/cloudwatch/latest/monitoring/working_with_metrics.html)

## 💡 Best Practices

1. **Redis Cache**:
   - Dùng TTL phù hợp (5 phút cho search, 1 giờ cho embedding)
   - Monitor cache hit rate (target >80%)
   - Invalidate cache khi update user

2. **Image Quality**:
   - Yêu cầu user chụp nhiều góc độ (min 5 ảnh)
   - Reject ảnh ngay nếu quality không đạt
   - Log warnings để cải thiện hệ thống

3. **Step Functions**:
   - Dùng cho workflows phức tạp >3 bước
   - Set timeout hợp lý (30s identify, 5min enroll)
   - Enable X-Ray tracing

4. **Monitoring**:
   - Set alarms cho metrics quan trọng
   - Review dashboard hàng ngày
   - Archive logs cũ (>30 ngày)

---

**Cập nhật**: 20/11/2025  
**Contact**: hoangphuc173@github.com
