# Hướng Dẫn Triển Khai AWS Lambda

Hướng dẫn triển khai các Lambda functions cho hệ thống Nhận Diện Khuôn Mặt.

---

## Điều Kiện Tiên Quyết

- ✅ Cơ sở hạ tầng đã được triển khai (Cognito, S3, DynamoDB)
- AWS CLI đã được cấu hình
- Python 3.11+
- PowerShell (để chạy script build)

---

## Kiến Trúc

**4 Lambda Functions**:
1. **auth-handler**: Đăng ký, đăng nhập, xác thực người dùng
2. **enroll-handler**: Đăng ký khuôn mặt với Rekognition
3. **identify-handler**: Nhận diện khuôn mặt
4. **people-handler**: Quản lý thông tin người dùng (CRUD)

---

## Bước 1: Build Lambda Layer

Lambda Layer chứa các thư viện Python (FastAPI, Pillow, boto3, v.v.)

### Sử Dụng Script Build

```bash
# Windows
scripts\utilities\build-layer.ps1

# Linux/Mac
chmod +x scripts/utilities/build-layer.sh
scripts/utilities/build-layer.sh
```

Lệnh này tạo file `backend/layer.zip` (~50MB)

### Build Thủ Công (nếu script lỗi)

```bash
cd backend

# Tạo thư mục layer
mkdir -p layer/python

# Cài đặt dependencies
pip install -r requirements.txt -t layer/python/

# Zip layer
cd layer
zip -r ../layer.zip python/
cd ..
```

### Upload Layer lên AWS

```bash
# Upload layer
aws lambda publish-layer-version \
  --layer-name python-deps \
  --description "Python dependencies for face recognition" \
  --zip-file fileb://backend/layer.zip \
  --compatible-runtimes python3.11

# Lưu ARN của layer
LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name python-deps \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

echo $LAYER_ARN
```

---

## Bước 2: Lấy Thông Tin Cơ Sở Hạ Tầng

Lấy các giá trị từ CDK deployment:

```bash
# Lấy Cognito User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Lấy Cognito Client ID  
CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text)

# Lấy S3 Bucket
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Lấy DynamoDB Table
DYNAMODB_TABLE=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DynamoDBTableName`].OutputValue' \
  --output text)

# Lấy Rekognition Collection
COLLECTION_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`RekognitionCollectionId`].OutputValue' \
  --output text)

echo "USER_POOL_ID=$USER_POOL_ID"
echo "CLIENT_ID=$CLIENT_ID"
echo "S3_BUCKET=$S3_BUCKET"
echo "DYNAMODB_TABLE=$DYNAMODB_TABLE"
echo "COLLECTION_ID=$COLLECTION_ID"
```

---

## Bước 3: Triển Khai Auth Handler

### Đóng Gói Function

```bash
cd backend/src/auth
zip -r auth-handler.zip .
cd ../../..
```

### Tạo Lambda Function

```bash
# Lấy IAM Role ARN từ CDK outputs
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaExecutionRoleArn`].OutputValue' \
  --output text)

# Tạo function
aws lambda create-function \
  --function-name auth-handler \
  --runtime python3.11 \
  --handler main.lambda_handler \
  --role $ROLE_ARN \
  --zip-file fileb://backend/src/auth/auth-handler.zip \
  --timeout 30 \
  --memory-size 512 \
  --layers $LAYER_ARN \
  --environment Variables="{
    COGNITO_USER_POOL_ID=$USER_POOL_ID,
    COGNITO_CLIENT_ID=$CLIENT_ID,
    REGION=us-east-1
  }"
```

---

## Bước 4: Triển Khai Enroll Handler

```bash
cd backend/src/enroll
zip -r enroll-handler.zip .
cd ../../..

aws lambda create-function \
  --function-name enroll-handler \
  --runtime python3.11 \
  --handler main.lambda_handler \
  --role $ROLE_ARN \
  --zip-file fileb://backend/src/enroll/enroll-handler.zip \
  --timeout 60 \
  --memory-size 1024 \
  --layers $LAYER_ARN \
  --environment Variables="{
    S3_BUCKET=$S3_BUCKET,
    DYNAMODB_TABLE=$DYNAMODB_TABLE,
    REKOGNITION_COLLECTION=$COLLECTION_ID,
    REGION=us-east-1
  }"
```

---

## Bước 5: Triển Khai Identify Handler

```bash
cd backend/src/identify
zip -r identify-handler.zip .
cd ../../..

aws lambda create-function \
  --function-name identify-handler \
  --runtime python3.11 \
  --handler main.lambda_handler \
  --role $ROLE_ARN \
  --zip-file fileb://backend/src/identify/identify-handler.zip \
 --timeout 30 \
  --memory-size 512 \
  --layers $LAYER_ARN \
  --environment Variables="{
    REKOGNITION_COLLECTION=$COLLECTION_ID,
    DYNAMODB_TABLE=$DYNAMODB_TABLE,
    REGION=us-east-1
  }"
```

---

## Bước 6: Triển Khai People Handler

```bash
cd backend/src/people
zip -r people-handler.zip .
cd ../../..

aws lambda create-function \
  --function-name people-handler \
  --runtime python3.11 \
  --handler main.lambda_handler \
  --role $ROLE_ARN \
  --zip-file fileb://backend/src/people/people-handler.zip \
  --timeout 30 \
  --memory-size 256 \
  --layers $LAYER_ARN \
  --environment Variables="{
    DYNAMODB_TABLE=$DYNAMODB_TABLE,
    S3_BUCKET=$S3_BUCKET,
    REGION=us-east-1
  }"
```

---

## Bước 7: Thiết Lập API Gateway

### Tạo API

```bash
# Tạo REST API
API_ID=$(aws apigateway create-rest-api \
  --name face-recognition-api \
  --description "Face Recognition API" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' \
  --output text)

# Lấy root resource
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' \
  --output text)
```

### Tạo Auth Resource

```bash
# Tạo resource /auth
AUTH_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part auth \
  --query 'id' \
  --output text)

# Tạo phương thức POST
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $AUTH_RESOURCE \
  --http-method POST \
  --authorization-type NONE

# Tích hợp với Lambda
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $AUTH_RESOURCE \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$(aws lambda get-function --function-name auth-handler --query 'Configuration.FunctionArn' --output text)/invocations

# Cấp quyền cho API Gateway gọi Lambda
aws lambda add-permission \
  --function-name auth-handler \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*"
```

### Triển Khai API

```bash
# Deploy tới stage 'prod'
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod

# Lấy API URL
API_URL="https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"
echo "API Gateway URL: $API_URL"
```

---

## Bước 8: Kiểm Tra Lambda Functions

### Test Auth Handler

```bash
# Gọi trực tiếp
aws lambda invoke \
  --function-name auth-handler \
  --payload '{"action":"health"}' \
  response.json

cat response.json
```

### Test qua API Gateway

```bash
# Test đăng ký
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

---

## Bước 9: Bật CloudWatch Logs

```bash
# Cập nhật logging cho từng function
aws lambda update-function-configuration \
  --function-name auth-handler \
  --logging-config LogFormat=JSON,LogGroup=/aws/lambda/auth-handler

aws lambda update-function-configuration \
  --function-name enroll-handler \
  --logging-config LogFormat=JSON,LogGroup=/aws/lambda/enroll-handler

aws lambda update-function-configuration \
  --function-name identify-handler \
  --logging-config LogFormat=JSON,LogGroup=/aws/lambda/identify-handler

aws lambda update-function-configuration \
  --function-name people-handler \
  --logging-config LogFormat=JSON,LogGroup=/aws/lambda/people-handler
```

---

## Cập Nhật Lambda Functions

Để cập nhật code:

```bash
# Đóng gói lại
cd backend/src/auth
zip -r auth-handler.zip .

# Cập nhật function
aws lambda update-function-code \
  --function-name auth-handler \
  --zip-file fileb://auth-handler.zip
```

---

## Giám Sát

### Xem Logs

```bash
# Theo dõi logs
aws logs tail /aws/lambda/auth-handler --follow
```

### Xem Metrics

```bash
# Lấy số lần gọi
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=auth-handler \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-12-31T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

---

## Xử Lý Sự Cố

### "Task timed out after 30.00 seconds"

Tăng timeout:
```bash
aws lambda update-function-configuration \
  --function-name FUNCTION_NAME \
  --timeout 60
```

### "Runtime exited with error: exit status 1"

Kiểm tra logs:
```bash
aws logs tail /aws/lambda/FUNCTION_NAME --since 10m
```

### Lỗi không tìm thấy module

Kiểm tra layer đã được gắn chưa:
```bash
aws lambda get-function-configuration \
  --function-name FUNCTION_NAME \
  --query 'Layers'
```

---

## Bước Tiếp Theo

Sau khi triển khai Lambda:

1. ✅ Lưu API Gateway URL
2. 🚀 Triển khai frontend với API URL: Xem `docs/AMPLIFY_DEPLOYMENT_VI.md`
3. 🧪 Kiểm tra toàn diện: Xem `docs/AWS_TESTING_GUIDE_VI.md`
