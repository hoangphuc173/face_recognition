# Triển Khai Cơ Sở Hạ Tầng AWS (CDK)

Hướng dẫn triển khai cơ sở hạ tầng AWS sử dụng AWS CDK.

---

## Điều Kiện Tiên Quyết

- **Node.js 18+** và npm
- **AWS CLI** đã được cấu hình: `aws configure`
- **AWS CDK CLI**: `npm install -g aws-cdk`
- **Quyền Admin** trong tài khoản AWS
- **Docker** (để đóng gói Lambda - tùy chọn)

---

## Bước 1: Thiết Lập Dự Án CDK

### Cài Đặt Dependencies

```bash
cd infrastructure
npm install
```

### Cấu Hình Môi Trường

Tạo file `.env`:

```bash
cd infrastructure

# Windows
echo AWS_ACCOUNT_ID=YOUR_ACCOUNT_ID > .env
echo AWS_REGION=us-east-1 >> .env
echo ENVIRONMENT=prod >> .env
echo PROJECT_NAME=face-recognition >> .env

# Linux/Mac
cat > .env << EOF
AWS_ACCOUNT_ID=YOUR_ACCOUNT_ID
AWS_REGION=us-east-1
ENVIRONMENT=prod
PROJECT_NAME=face-recognition
EOF
```

**Lấy AWS Account ID của bạn**:
```bash
aws sts get-caller-identity --query Account --output text
```

---

## Bước 2: Bootstrap CDK

Bootstrap CDK trong tài khoản (chỉ cần làm 1 lần):

```bash
cd infrastructure

# Bootstrap
cdk bootstrap

# Hoặc với account/region cụ thể
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

Lệnh này sẽ tạo:
- S3 bucket cho CDK assets
- ECR repository cho Docker images
- IAM roles cho việc deployment
- CloudFormation stack: `CDKToolkit`

**Kiểm tra bootstrap**:
```bash
aws cloudformation describe-stacks --stack-name CDKToolkit
```

---

## Bước 3: Xem Lại Mã Nguồn Cơ Sở Hạ Tầng

### Kiểm Tra Main Stack

```bash
# Xem mã nguồn
code infrastructure/lib/main-stack.ts

# Hoặc đọc bằng cat/type
cat infrastructure/lib/main-stack.ts
```

**Các tài nguyên được tạo bởi CDK**:
- ✅ Cognito User Pool + Client
- ✅ S3 Bucket (được mã hóa với KMS)
- ✅ DynamoDB Table (được mã hóa)
- ✅ Rekognition Face Collection
- ✅ IAM Roles cho Lambda
- ✅ KMS Keys
- ✅ API Gateway (cấu hình cơ bản)

### Build TypeScript

```bash
cd infrastructure
npm run build
```

---

## Bước 4: Xem Trước Thay Đổi

```bash
cd infrastructure

# Xem những gì sẽ được tạo
cdk diff

# Tạo CloudFormation template
cdk synth

# Xem template
cdk synth > template.yaml
code template.yaml
```

---

## Bước 5: Triển Khai Cơ Sở Hạ Tầng

### Lựa Chọn A: Triển Khai Tất Cả Stacks

```bash
cd infrastructure

# Triển khai không cần hỏi xác nhận
cdk deploy --all --require-approval never

# Hoặc triển khai có xem lại
cdk deploy --all
```

### Lựa Chọn B: Triển Khai Stack Cụ Thể

```bash
# Chỉ triển khai main stack
cdk deploy FaceRecognitionStack-prod

# Triển khai với tham số
cdk deploy FaceRecognitionStack-prod \
  --parameters environment=prod \
  --parameters projectName=face-recognition
```

**Chờ quá trình triển khai** (5-10 phút)

---

## Bước 6: Lưu Các Output

Sau khi triển khai, lưu lại các thông tin quan trọng:

```bash
# Lấy tất cả outputs
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs' \
  > infrastructure/outputs.json

# Xem outputs
cat infrastructure/outputs.json
```

**Các output quan trọng**:
- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito Client ID  
- `S3BucketName`: Tên S3 bucket chứa ảnh
- `DynamoDBTableName`: Tên bảng DynamoDB
- `RekognitionCollectionId`: ID bộ sưu tập Rekognition
- `ApiGatewayUrl`: API Gateway endpoint (sau khi deploy Lambda)

**Lưu các giá trị này** - bạn sẽ cần chúng để cấu hình Lambda và frontend!

---

## Bước 7: Xác Minh Cơ Sở Hạ Tầng

### Xác Minh CloudFormation Stack

```bash
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].StackStatus'
```

Mong đợi: `CREATE_COMPLETE` hoặc `UPDATE_COMPLETE`

### Xác Minh Cognito User Pool

```bash
# Lấy outputs
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Xem thông tin user pool
aws cognito-idp describe-user-pool --user-pool-id $USER_POOL_ID
```

### Xác Minh S3 Bucket

```bash
# Lấy tên bucket
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Liệt kê bucket (nên rỗng)
aws s3 ls s3://$BUCKET_NAME

# Kiểm tra mã hóa
aws s3api get-bucket-encryption --bucket $BUCKET_NAME
```

### Xác Minh DynamoDB Table

```bash
# Lấy tên table
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DynamoDBTableName`].OutputValue' \
  --output text)

# Xem thông tin table
aws dynamodb describe-table --table-name $TABLE_NAME

# Quét table (nên rỗng)
aws dynamodb scan --table-name $TABLE_NAME
```

### Xác Minh Rekognition Collection

```bash
# Liệt kê collections
aws rekognition list-collections

# Xem thông tin collection
aws rekognition describe-collection --collection-id face-recognition-collection
```

---

## Bước 8: Tạo Cognito Groups

Tạo các nhóm người dùng cho phân quyền (RBAC):

```bash
# Lấy User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Tạo nhóm Admin
aws cognito-idp create-group \
  --user-pool-id $USER_POOL_ID \
  --group-name Admin \
  --description "Administrator group with full permissions"

# Tạo nhóm Staff
aws cognito-idp create-group \
  --user-pool-id $USER_POOL_ID \
  --group-name Staff \
  --description "Staff group with limited permissions"

# Tạo nhóm Guest
aws cognito-idp create-group \
  --user-pool-id $USER_POOL_ID \
  --group-name Guest \
  --description "Guest group with read-only permissions"

# Kiểm tra các nhóm
aws cognito-idp list-groups --user-pool-id $USER_POOL_ID
```

---

## Giám Sát & Logs

### CloudWatch Dashboard

CDK tạo CloudWatch dashboard:

```bash
# Liệt kê dashboards
aws cloudwatch list-dashboards

# Xem trong console
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:
```

### CloudWatch Logs

```bash
# Liệt kê log groups đã tạo
aws logs describe-log-groups \
  --log-group-name-prefix /aws/face-recognition
```

---

## Ước Tính Chi Phí

**Chi phí hàng tháng** cho cơ sở hạ tầng (không có traffic):

| Dịch Vụ | Chi Phí |
|---------|---------|
| Cognito User Pool | $0 (50K MAU miễn phí) |
| S3 Bucket | ~$1 (5GB miễn phí) |
| DynamoDB | ~$2.50 (25GB miễn phí) |
| Rekognition Collection | $0 (không tính phí khi không dùng) |
| CloudWatch Logs | ~$0.50 |
| KMS Keys | $1/key/tháng |
| **Tổng Cộng** | **~$5-10/tháng** |

**Với traffic** (1000 requests/ngày):
- Lambda: ~$10
- API Gateway: ~$3.50
- Rekognition: ~$1 (1000 khuôn mặt)
- Data transfer: ~$5
- **Tổng Cộng**: **~$25-30/tháng**

---

## Cập Nhật Cơ Sở Hạ Tầng

Để cập nhật sau khi sửa đổi mã nguồn:

```bash
cd infrastructure

# Build
npm run build

# Xem trước thay đổi
cdk diff

# Triển khai cập nhật
cdk deploy --all
```

---

## Rollback (Khôi Phục)

Nếu triển khai thất bại:

```bash
# CloudFormation tự động rollback khi lỗi
# Kiểm tra trạng thái
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod

# Nếu bị kẹt, tiếp tục rollback
aws cloudformation continue-update-rollback \
  --stack-name FaceRecognitionStack-prod
```

---

## Xử Lý Sự Cố

### "Unable to resolve AWS account"

**Giải pháp**: Cấu hình AWS CLI
```bash
aws configure
# Nhập access key, secret key, region
```

### "CDK bootstrap required"

**Giải pháp**: Bootstrap CDK
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### "Insufficient permissions"

**Giải pháp**: Đảm bảo IAM user có quyền:
- CloudFormationFullAccess
- IAMFullAccess
- S3FullAccess
- DynamoDBFullAccess
- CognitoIdpFullAccess
- RekognitionFullAccess

### "Stack already exists"

Nếu deploy lại sau khi cleanup:
```bash
# Chờ stack cũ xóa xong
aws cloudformation wait stack-delete-complete \
  --stack-name FaceRecognitionStack-prod

# Sau đó deploy lại
cdk deploy
```

---

## Bước Tiếp Theo

Sau khi triển khai thành công cơ sở hạ tầng:

1. ✅ **Lưu outputs** vào `infrastructure/outputs.json`
2. 📋 **Triển khai Lambda functions**: Xem `docs/AWS_LAMBDA_DEPLOYMENT_VI.md`
3. 🚀 **Triển khai frontend**: Xem `docs/AMPLIFY_DEPLOYMENT_VI.md`
4. 👤 **Tạo người dùng**: Xem `docs/AWS_TESTING_GUIDE_VI.md`

---

## Dọn Dẹp

Để xóa toàn bộ cơ sở hạ tầng:

```bash
cd infrastructure
cdk destroy --all

# Xác nhận xóa khi được hỏi
```

Xem `docs/AWS_CLEANUP_GUIDE_VI.md` để biết hướng dẫn dọn dẹp chi tiết.
