# Hướng Dẫn Xử Lý Sự Cố AWS

Các vấn đề thường gặp và giải pháp cho việc triển khai hệ thống Nhận Diện Khuôn Mặt.

---

## Các Vấn Đề Khi Triển Khai

### CDK Bootstrap Thất Bại

**Lỗi**: `Unable to resolve AWS account`

**Giải pháp**:
```bash
# Cấu hình AWS CLI
aws configure
# Nhập: Access Key, Secret Key, Region

# Xác minh
aws sts get-caller-identity
```

---

**Lỗi**: `Need to perform AWS calls for account XXX, but no credentials configured`

**Giải pháp**:
```bash
# Export credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Hoặc dùng AWS profile
aws configure --profile myprofile
export AWS_PROFILE=myprofile
```

---

### CloudFormation Stack Bị Kẹt

**Lỗi**: `Stack is in UPDATE_ROLLBACK_FAILED state`

**Giải pháp**:
```bash
# Tiếp tục rollback
aws cloudformation continue-update-rollback \
  --stack-name FaceRecognitionStack-prod

# Chờ hoàn tất
aws cloudformation wait stack-rollback-complete \
  --stack-name FaceRecognitionStack-prod

# Sau đó xóa
aws cloudformation delete-stack \
  --stack-name FaceRecognitionStack-prod
```

---

**Lỗi**: `Stack deletion stuck`

**Giải pháp**:
```bash
# Kiểm tra sự kiện stack
aws cloudformation describe-stack-events \
  --stack-name FaceRecognitionStack-prod \
  --max-items 10

# Nếu resource cụ thể bị lỗi, xóa thủ công rồi thử xóa stack lại
```

---

### Lambda Deployment Thất Bại

**Lỗi**: `InvalidParameterValueException: Unzipped size must be smaller than 262144000 bytes`

**Giải pháp**: Gói Lambda hoặc layer của bạn quá lớn.

```bash
# Kiểm tra kích thước layer
ls -lh backend/layer.zip

# Nếu > 250MB, tối ưu hóa dependencies:
pip install -r requirements.txt -t layer/python/ --no-deps
# Sau đó thêm các deps thiếu từng cái một
```

---

**Lỗi**: `ResourceConflictException: Function already exists`

**Giải pháp**:
```bash
# Xóa function hiện tại trước
aws lambda delete-function --function-name auth-handler

# Sau đó deploy lại
aws lambda create-function ...
```

---

## Các Vấn Đề Khi Chạy (Runtime)

### Lambda Timeout

**Lỗi**: `Task timed out after 30.00 seconds`

**Giải pháp**:
```bash
# Tăng timeout
aws lambda update-function-configuration \
  --function-name enroll-handler \
  --timeout 60

# Hoặc trong mã CDK:
# timeout: cdk.Duration.seconds(60)
```

---

### Lambda Hết Bộ Nhớ (Out of Memory)

**Lỗi**: `Process exited after running out of memory`

**Giải pháp**:
```bash
# Tăng bộ nhớ
aws lambda update-function-configuration \
  --function-name identify-handler \
  --memory-size 1024

# Giám sát sử dụng bộ nhớ
aws lambda get-function-configuration \
  --function-name identify-handler \
  --query 'MemorySize'
```

---

### Không Tìm Thấy Module

**Lỗi**: `Unable to import module 'main': No module named 'fastapi'`

**Giải pháp**: Layer chưa được gắn hoặc không chính xác.

```bash
# Kiểm tra layer
aws lambda get-function-configuration \
  --function-name auth-handler \
  --query 'Layers'

# Nếu chưa có layer, thêm vào
aws lambda update-function-configuration \
  --function-name auth-handler \
  --layers $LAYER_ARN

# Nếu layer đã có, build lại
scripts\utilities\build-layer.ps1
# Sau đó cập nhật version layer
```

---

### Từ Chối Quyền (Permission Denied)

**Lỗi**: `User is not authorized to perform: lambda:InvokeFunction`

**Giải pháp**:
```bash
# Thêm quyền cho API Gateway gọi Lambda
aws lambda add-permission \
  --function-name auth-handler \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:REGION:ACCOUNT:API_ID/*/*"
```

---

## Các Vấn Đề API Gateway

### Lỗi CORS

**Lỗi**: `No 'Access-Control-Allow-Origin' header is present`

**Giải pháp**:
```bash
# Bật CORS cho resource
aws apigateway update-integration-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --status-code 200 \
  --patch-operations \
    op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value="'*'"
```

Hoặc trong phản hồi Lambda:
```python
return {
    "statusCode": 200,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
    },
    "body": json.dumps(data)
}
```

---

### 502 Bad Gateway

**Lỗi**: `{"message": "Internal server error"}`

**Nguyên nhân có thể**:
1. Lambda timeout
2. Lambda function lỗi
3. Định dạng phản hồi Lambda không hợp lệ

**Giải pháp**:
```bash
# Kiểm tra Lambda logs
aws logs tail /aws/lambda/auth-handler --since 10m

# Kiểm tra định dạng phản hồi Lambda (phải là proxy format)
{
  "statusCode": 200,
  "headers": {...},
  "body": "..." # Phải là chuỗi (string), không phải object!
}
```

---

### 403 Forbidden

**Lỗi**: `User is not authorized to access this resource`

**Giải pháp**: Kiểm tra cấu hình Cognito authorizer.

```bash
# Xác minh authorizer đã được cấu hình
aws apigateway get-authorizers --rest-api-id $API_ID

# Test với JWT token hợp lệ
curl -H "Authorization: Bearer $JWT_TOKEN" $API_URL/people
```

---

## Các Vấn Đề Cognito

### Người Dùng Chưa Được Xác Nhận

**Lỗi**: `User is not confirmed`

**Giải pháp**:
```bash
# Xác nhận người dùng thủ công
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com

# Hoặc bật auto-confirm trong cài đặt user pool
```

---

### Mật Khẩu Không Hợp Lệ

**Lỗi**: `Password does not conform to policy`

**Giải pháp**: Mật khẩu phải đáp ứng yêu cầu:
- Tối thiểu 8 ký tự
- Ít nhất 1 chữ hoa
- Ít nhất 1 chữ thường
- Ít nhất 1 số
- Ít nhất 1 ký tự đặc biệt

---

### Quá Nhiều Yêu Cầu

**Lỗi**: `TooManyRequestsException: Rate exceeded`

**Giải pháp**: Cognito có giới hạn tốc độ. Chờ và thử lại, hoặc yêu cầu tăng giới hạn.

---

## Các Vấn Đề S3

### Từ Chối Truy Cập (Access Denied)

**Lỗi**: `Access Denied` khi upload lên S3

**Giải pháp**:
```bash
# Kiểm tra bucket policy
aws s3api get-bucket-policy --bucket $BUCKET_NAME

# Kiểm tra Lambda role có quyền S3
aws iam get-role-policy \
  --role-name lambda-execution-role \
  --policy-name S3Access
  
# Thêm quyền S3 cho Lambda role nếu thiếu
```

---

### Bucket Không Rỗng

**Lỗi**: `The bucket you tried to delete is not empty`

**Giải pháp**:
```bash
# Làm rỗng bucket trước
aws s3 rm s3://$BUCKET_NAME --recursive

# Sau đó xóa
aws s3 rb s3://$BUCKET_NAME
```

---

## Các Vấn Đề DynamoDB

### Item Không Tồn Tại

**Lỗi**: `Item does not exist`

**Giải pháp**:
```bash
# Xác minh table tồn tại
aws dynamodb describe-table --table-name face-recognition-users

# Quét table
aws dynamodb scan --table-name face-recognition-users

# Kiểm tra định dạng partition key
```

---

### ProvisionedThroughputExceededException

**Lỗi**: `The level of configured provisioned throughput for the table was exceeded`

**Giải pháp**:
```bash
# Chuyển sang on-demand billing
aws dynamodb update-table \
  --table-name face-recognition-users \
  --billing-mode PAY_PER_REQUEST

# Hoặc tăng provisioned capacity
aws dynamodb update-table \
  --table-name face-recognition-users \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10
```

---

## Các Vấn Đề Rekognition

### Không Tìm Thấy Khuôn Mặt

**Lỗi**: `InvalidParameterException: There are no faces in the image`

**Giải pháp**:
- Chất lượng ảnh quá thấp
- Khuôn mặt quá nhỏ (< 100x100 pixels)
- Khuôn mặt bị nghiêng (> 30° pitch/roll/yaw)
- Ánh sáng kém
- Khuôn mặt bị che khuất

**Cải thiện ảnh**:
- Ánh sáng tốt
- Khuôn mặt ở giữa
- Nhìn thẳng vào camera
- Độ phân giải tối thiểu 640x480

---

### Không Tìm Thấy Collection

**Lỗi**: `ResourceNotFoundException: Collection id: face-recognition-collection not found`

**Giải pháp**:
```bash
# Tạo collection
aws rekognition create-collection \
  --collection-id face-recognition-collection

# Xác minh
aws rekognition describe-collection \
  --collection-id face-recognition-collection
```

---

## Các Vấn Đề Amplify

### Build Thất Bại

**Lỗi**: `Build failed`

**Giải pháp**:
```bash
# Kiểm tra build logs trong Amplify Console

# Nguyên nhân thường gặp:
# 1. Thiếu biến môi trường
# 2. Sai phiên bản Node
# 3. Lệnh build sai
# 4. Hết bộ nhớ
```

Sửa trong `amplify.yml`:
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend/web
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/web/.next
    files:
      - '**/*'
```

---

### Biến Môi Trường Không Hoạt Động

**Lỗi**: API calls gọi đến localhost thay vì production API

**Giải pháp**:
```bash
# Trong Amplify Console:
# 1. Vào Environment variables
# 2. Thêm: NEXT_PUBLIC_API_URL=https://API_ID.execute-api.us-east-1.amazonaws.com/prod
# 3. Deploy lại

# Xác minh trong browser console:
console.log(process.env.NEXT_PUBLIC_API_URL)
```

---

## Debugging Chung

### Bật Logging Chi Tiết

```bash
# Lambda
aws lambda update-function-configuration \
  --function-name auth-handler \
  --environment Variables='{DEBUG=true,LOG_LEVEL=DEBUG}'

# API Gateway
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/\*/logging/dataTrace,value=true \
    op=replace,path=/\*/logging/loglevel,value=INFO
```

### Kiểm Tra CloudWatch Logs

```bash
# Theo dõi logs
aws logs tail /aws/lambda/auth-handler --follow

# Lọc logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/auth-handler \
  --filter-pattern "ERROR"

# Lấy khoảng thời gian cụ thể
aws logs filter-log-events \
  --log-group-name /aws/lambda/auth-handler \
  --start-time $(date -d '1 hour ago' +%s)000
```

---

## Nhận Trợ Giúp

Nếu vẫn bị kẹt:

1. **Kiểm tra CloudWatch Logs**: Thông tin lỗi chi tiết nhất
2. **Kiểm tra AWS Service Health**: https://status.aws.amazon.com
3. **Xem lại IAM Permissions**: Đảm bảo roles có đủ quyền
4. **Test Local**: Dùng môi trường local để cô lập vấn đề
5. **AWS Support**: Tạo support ticket nếu cần

---

## Script Chẩn Đoán Nhanh

```bash
#!/bin/bash
# diagnose.sh - Kiểm tra sức khỏe nhanh

echo "=== CloudFormation Stack ==="
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].StackStatus'

echo "=== Lambda Functions ==="
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,Runtime,LastModified]' \
  --output table

echo "=== API Gateway ==="
aws apigateway get-rest-apis \
  --query 'items[*].[name,id]' \
  --output table

echo "=== Cognito User Pools ==="
aws cognito-idp list-user-pools --max-results 10 \
  --query 'UserPools[*].[Name,Id]' \
  --output table

echo "=== Các Lỗi Lambda Gần Đây ==="
aws logs filter-log-events \
  --log-group-name /aws/lambda/auth-handler \
  --filter-pattern "ERROR" \
  --max-items 5
```

Chạy: `chmod +x diagnose.sh && ./diagnose.sh`
