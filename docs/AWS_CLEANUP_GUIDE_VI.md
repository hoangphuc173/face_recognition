# Hướng Dẫn Xóa AWS Resources

Hướng dẫn xóa toàn bộ AWS resources cũ trước khi deploy lại hệ thống.

---

## ⚠️ Cảnh Báo

> [!CAUTION]
> **Cảnh Báo Mất Dữ Liệu**
> - Xóa resources sẽ **MẤT TẤT CẢ DỮ LIỆU**
> - Cognito users: Tất cả tài khoản người dùng bị xóa
> - S3 bucket: Tất cả ảnh khuôn mặt bị xóa
> - DynamoDB: Tất cả hồ sơ người dùng bị xóa
> - **SAO LƯU DỮ LIỆU TRƯỚC KHI XÓA** nếu cần giữ lại

> [!WARNING]
> **Chi Phí AWS**
> - Xóa đúng cách để tránh bị tính phí tiếp
> - Xác minh tất cả resources đã bị xóa
> - Kiểm tra AWS billing dashboard sau khi xóa

---

## Yêu Cầu

- AWS CLI đã cấu hình: `aws configure`
- Quyền Admin trong AWS account
- Biết region đang dùng (thường là `us-east-1`)

## Bước 1: Liệt Kê Tất Cả Resources Hiện Tại

### CloudFormation Stacks

```bash
# Liệt kê tất cả stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[*].[StackName,StackStatus,CreationTime]" \
  --output table
```

Tìm các stacks như:
- `FaceRecognitionStack-*`
- `FaceRecStack`
- `CDKToolkit` (CDK bootstrap stack - **KHÔNG XÓA**)

### Lambda Functions

```bash
# Liệt kê tất cả Lambda functions
aws lambda list-functions \
  --query "Functions[*].[FunctionName,Runtime,LastModified]" \
  --output table
```

Tìm:
- `auth-handler`
- `enroll-handler`
- `identify-handler`
- `people-handler`

### API Gateway

```bash
# Liệt kê REST APIs
aws apigateway get-rest-apis \
  --query "items[*].[name,id,createdDate]" \
  --output table
```

Tìm: `face-recognition-api` hoặc tương tự

### Cognito User Pools

```bash
#Liệt kê User Pools
aws cognito-idp list-user-pools \
  --max-results 20 \
  --query "UserPools[*].[Name,Id,CreationDate]" \
  --output table
```

### S3 Buckets

```bash
# Liệt kê buckets (lọc theo tên)
aws s3 ls | grep face

# HOẶC bucket cụ thể
aws s3 ls s3://face-recognition-images-bucket
```

### DynamoDB Tables

```bash
# Liệt kê tables
aws dynamodb list-tables \
  --query "TableNames" \
  --output table
```

Tìm: `face-recognition-users` hoặc tương tự

### Lambda Layers

```bash
# Liệt kê layers
aws lambda list-layers \
  --query "Layers[*].[LayerName,LatestMatchingVersion.Version]" \
  --output table
```

---

## Bước 2: Sao Lưu Dữ Liệu (Tùy Chọn)

### Sao Lưu Cognito Users

```bash
# Export danh sách users
aws cognito-idp list-users \
  --user-pool-id YOUR_POOL_ID \
  > cognito-users-backup.json
```

### Sao Lưu DynamoDB Data

```bash
# Export dữ liệu table
aws dynamodb scan \
  --table-name face-recognition-users \
  > dynamodb-backup.json
```

### Sao Lưu S3 Images

```bash
# Tải xuống tất cả images
aws s3 sync s3://your-bucket-name ./s3-backup/
```

---

## Bước 3: Xóa Resources

### Phương Án A: Xóa Qua CDK (Khuyến Nghị)

Nếu resources được deploy bằng CDK:

```bash
cd infrastructure

# Liệt kê CDK stacks
cdk list

# Xóa tất cả stacks
cdk destroy --all

# Xác nhận xóa khi được hỏi
```

**Chờ hoàn tất** (có thể mất 5-10 phút)

### Phương Án B: Xóa Thủ Công

Nếu CDK destroy thất bại hoặc một số resources không được tạo bởi CDK:

#### Xóa CloudFormation Stacks

```bash
# Xóa main stack
aws cloudformation delete-stack --stack-name FaceRecognitionStack-prod

# Chờ xóa hoàn tất
aws cloudformation wait stack-delete-complete --stack-name FaceRecognitionStack-prod

# Kiểm tra trạng thái
aws cloudformation describe-stacks --stack-name FaceRecognitionStack-prod
```

Nếu stack bị kẹt:

```bash
# Buộc tiếp tục rollback
aws cloudformation continue-update-rollback --stack-name FaceRecognitionStack-prod

# Sau đó xóa lại
aws cloudformation delete-stack --stack-name FaceRecognitionStack-prod
```

#### Xóa Lambda Functions

```bash
# Xóa từng function
aws lambda delete-function --function-name auth-handler
aws lambda delete-function --function-name enroll-handler
aws lambda delete-function --function-name identify-handler
aws lambda delete-function --function-name people-handler

# Xác minh đã xóa
aws lambda list-functions --query "Functions[*].FunctionName"
```

#### Xóa Lambda Layers

```bash
# Xóa tất cả versions của layer
aws lambda delete-layer-version \
  --layer-name python-deps \
  --version-number 1

# Lặp lại cho tất cả versions
```

#### Xóa API Gateway

```bash
# Lấy API ID
aws apigateway get-rest-apis --query "items[?name=='face-recognition-api'].id" --output text

# Xóa API
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID

# Xác minh đã xóa
aws apigateway get-rest-apis
```

#### Xóa Cognito User Pool

```bash
# Xóa domain (nếu đã cấu hình)
aws cognito-idp delete-user-pool-domain \
  --user-pool-id YOUR_POOL_ID \
  --domain your-domain

# Xóa user pool
aws cognito-idp delete-user-pool --user-pool-id YOUR_POOL_ID

# Xác minh đã xóa
aws cognito-idp list-user-pools --max-results 20
```

#### Xóa S3 Bucket

```bash
# CẢNH BÁO: Xóa TẤT CẢ files trong bucket
aws s3 rb s3://your-bucket-name --force

# Với bucket có versioning
aws s3api delete-bucket \
  --bucket your-bucket-name \
  --region us-east-1

# Xác minh đã xóa
aws s3 ls
```

#### Xóa DynamoDB Table

```bash
# Xóa table
aws dynamodb delete-table --table-name face-recognition-users

# Chờ xóa xong
aws dynamodb wait table-not-exists --table-name face-recognition-users

# Xác minh đã xóa
aws dynamodb list-tables
```

#### Xóa IAM Roles

```bash
# Liệt kê Lambda execution roles
aws iam list-roles --query "Roles[?contains(RoleName,'Lambda')].[RoleName]" --output table

# Gỡ policies trước
aws iam list-attached-role-policies --role-name YOUR_ROLE_NAME
aws iam detach-role-policy --role-name YOUR_ROLE_NAME --policy-arn POLICY_ARN

# Xóa role
aws iam delete-role --role-name YOUR_ROLE_NAME
```

#### Xóa CloudWatch Log Groups

```bash
# Liệt kê log groups
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda \
  --query "logGroups[*].logGroupName" \
  --output table

# Xóa từng log group
aws logs delete-log-group --log-group-name /aws/lambda/auth-handler
aws logs delete-log-group --log-group-name /aws/lambda/enroll-handler
aws logs delete-log-group --log-group-name /aws/lambda/identify-handler
aws logs delete-log-group --log-group-name /aws/lambda/people-handler
```

---

## Bước 4: Xác Minh Đã Xóa Hoàn Tất

### Kiểm Tra CloudFormation

```bash
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE DELETE_FAILED \
  --query "StackSummaries[*].[StackName,StackStatus]" \
  --output table
```

Mong đợi: Không còn stacks liên quan đến face-recognition

### Kiểm Tra Lambda

```bash
aws lambda list-functions --query "Functions[*].FunctionName"
```

Mong đợi: Không còn auth/enroll/identify/people handlers

### Kiểm Tra API Gateway

```bash
aws apigateway get-rest-apis
```

Mong đợi: Không còn face-recognition-api

### Kiểm Tra Cognito

```bash
aws cognito-idp list-user-pools --max-results 20
```

Mong đợi: Không còn face-recognition user pools

### Kiểm Tra S3

```bash
aws s3 ls | grep face
```

Mong đợi: Không còn face-recognition buckets

### Kiểm Tra DynamoDB

```bash
aws dynamodb list-tables
```

Mong đợi: Không còn face-recognition tables

### Kiểm Tra Resource Tags

```bash
# Tìm resources còn lại với project tag
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=face-recognition
```

Mong đợi: Danh sách rỗng

---

## Xử Lý Sự Cố

### Xóa Stack Thất Bại

**Lỗi**: `Stack cannot be deleted while in UPDATE_ROLLBACK_FAILED state`

**Giải pháp**:
```bash
aws cloudformation continue-update-rollback --stack-name STACK_NAME
# Chờ rollback hoàn tất, sau đó xóa lại
aws cloudformation delete-stack --stack-name STACK_NAME
```

### Bucket Không Rỗng

**Lỗi**: `The bucket you tried to delete is not empty`

**Giải pháp**:
```bash
# Làm rỗng bucket trước
aws s3 rm s3://bucket-name --recursive
# Sau đó xóa
aws s3 rb s3://bucket-name
```

### Resources Vẫn Còn Tồn Tại

Nếu một số resources vẫn còn sau khi xóa CloudFormation:
1. Xóa thủ công các resources mồ côi (xem Bước 3B)
2. Kiểm tra resources ở các regions khác
3. Dùng AWS Console để kiểm tra trực quan

### Từ Chối Quyền

Đảm bảo AWS credentials có quyền admin:
```bash
aws sts get-caller-identity
# Nên hiển thị account ID của bạn

# Kiểm tra permissions
aws iam get-user
```

---

## Danh Sách Kiểm Tra Sau Khi Xóa

- [ ] Không còn CloudFormation stacks
- [ ] Không còn Lambda functions
- [ ] Không còn API Gateways
- [ ] Không còn Cognito User Pools
- [ ] Không còn S3 buckets
- [ ] Không còn DynamoDB tables
- [ ] Không còn IAM roles cho Lambda
- [ ] Không còn CloudWatch log groups
- [ ] AWS billing không còn tính phí cho các dịch vụ này

---

## Bước Tiếp Theo

Sau khi xóa thành công:
1. Xem `docs/AWS_INFRASTRUCTURE_DEPLOYMENT_VI.md` để deploy lại CDK
2. Xem `docs/AWS_LAMBDA_DEPLOYMENT_VI.md` để deploy Lambda
3. Xem `docs/AMPLIFY_DEPLOYMENT_VI.md` để deploy frontend
