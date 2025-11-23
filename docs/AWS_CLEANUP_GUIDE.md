# AWS Cleanup Guide

Hướng dẫn xóa toàn bộ AWS resources cũ trước khi deploy lại hệ thống.

---

## ⚠️ Warnings

> [!CAUTION]
> **Data Loss Warning**
> - Xóa resources sẽ MẤT TẤT CẢ DATA
> - Cognito users: All user accounts deleted
> - S3 bucket: All face images deleted
> - DynamoDB: All user profiles deleted
> - **BACKUP DATA TRƯỚC KHI XÓA** nếu cần giữ lại

> [!WARNING]
> **AWS Costs**
> - Xóa đúng cách để tránh bị charge tiếp
> - Verify tất cả resources đã bị xóa
> - Check AWS billing dashboard sau khi xóa

---

## Prerequisites

- AWS CLI configured: `aws configure`
- Admin permissions trong AWS account
- Biết region đang dùng (thường là `us-east-1`)

## Step 1: List All Existing Resources

### CloudFormation Stacks

```bash
# List all stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[*].[StackName,StackStatus,CreationTime]" \
  --output table
```

Look for stacks like:
- `FaceRecognitionStack-*`
- `FaceRecStack`
- `CDKToolkit` (CDK bootstrap stack - don't delete)

### Lambda Functions

```bash
# List all Lambda functions
aws lambda list-functions \
  --query "Functions[*].[FunctionName,Runtime,LastModified]" \
  --output table
```

Look for:
- `auth-handler`
- `enroll-handler`
- `identify-handler`
- `people-handler`

### API Gateway

```bash
# List REST APIs
aws apigateway get-rest-apis \
  --query "items[*].[name,id,createdDate]" \
  --output table
```

Look for: `face-recognition-api` or similar

### Cognito User Pools

```bash
# List User Pools
aws cognito-idp list-user-pools \
  --max-results 20 \
  --query "UserPools[*].[Name,Id,CreationDate]" \
  --output table
```

### S3 Buckets

```bash
# List buckets (filter by name)
aws s3 ls | grep face

# OR specific bucket
aws s3 ls s3://face-recognition-images-bucket
```

### DynamoDB Tables

```bash
# List tables
aws dynamodb list-tables \
  --query "TableNames" \
  --output table
```

Look for: `face-recognition-users` or similar

### Lambda Layers

```bash
# List layers
aws lambda list-layers \
  --query "Layers[*].[LayerName,LatestMatchingVersion.Version]" \
  --output table
```

---

## Step 2: Backup Data (Optional)

### Backup Cognito Users

```bash
# Export user pool users
aws cognito-idp list-users \
  --user-pool-id YOUR_POOL_ID \
  > cognito-users-backup.json
```

### Backup DynamoDB Data

```bash
# Export table data
aws dynamodb scan \
  --table-name face-recognition-users \
  > dynamodb-backup.json
```

### Backup S3 Images

```bash
# Download all images
aws s3 sync s3://your-bucket-name ./s3-backup/
```

---

## Step 3: Delete Resources

### Option A: Delete via CDK (Recommended)

If resources were deployed using CDK:

```bash
cd infrastructure

# List CDK stacks
cdk list

# Destroy all stacks
cdk destroy --all

# Confirm deletion when prompted
```

**Wait for completion** (can take 5-10 minutes)

### Option B: Manual Deletion

If CDK destroy fails or some resources weren't created by CDK:

#### Delete CloudFormation Stacks

```bash
# Delete main stack
aws cloudformation delete-stack --stack-name FaceRecognitionStack-prod

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name FaceRecognitionStack-prod

# Check status
aws cloudformation describe-stacks --stack-name FaceRecognitionStack-prod
```

If stack is stuck:

```bash
# Force continue rollback
aws cloudformation continue-update-rollback --stack-name FaceRecognitionStack-prod

# Then delete again
aws cloudformation delete-stack --stack-name FaceRecognitionStack-prod
```

#### Delete Lambda Functions

```bash
# Delete each function
aws lambda delete-function --function-name auth-handler
aws lambda delete-function --function-name enroll-handler
aws lambda delete-function --function-name identify-handler
aws lambda delete-function --function-name people-handler

# Verify deletion
aws lambda list-functions --query "Functions[*].FunctionName"
```

#### Delete Lambda Layers

```bash
# Delete all versions of a layer
aws lambda delete-layer-version \
  --layer-name python-deps \
  --version-number 1

# Repeat for all versions
```

#### Delete API Gateway

```bash
# Get API ID
aws apigateway get-rest-apis --query "items[?name=='face-recognition-api'].id" --output text

# Delete API
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID

# Verify deletion
aws apigateway get-rest-apis
```

#### Delete Cognito User Pool

```bash
# Delete domain (if configured)
aws cognito-idp delete-user-pool-domain \
  --user-pool-id YOUR_POOL_ID \
  --domain your-domain

# Delete user pool
aws cognito-idp delete-user-pool --user-pool-id YOUR_POOL_ID

# Verify deletion
aws cognito-idp list-user-pools --max-results 20
```

#### Delete S3 Bucket

```bash
# CAUTION: This deletes ALL files in bucket
aws s3 rb s3://your-bucket-name --force

# For bucket with versioning
aws s3api delete-bucket \
  --bucket your-bucket-name \
  --region us-east-1

# Verify deletion
aws s3 ls
```

#### Delete DynamoDB Table

```bash
# Delete table
aws dynamodb delete-table --table-name face-recognition-users

# Wait for deletion
aws dynamodb wait table-not-exists --table-name face-recognition-users

# Verify deletion
aws dynamodb list-tables
```

#### Delete IAM Roles

```bash
# List Lambda execution roles
aws iam list-roles --query "Roles[?contains(RoleName,'Lambda')].[RoleName]" --output table

# Detach policies first
aws iam list-attached-role-policies --role-name YOUR_ROLE_NAME
aws iam detach-role-policy --role-name YOUR_ROLE_NAME --policy-arn POLICY_ARN

# Delete role
aws iam delete-role --role-name YOUR_ROLE_NAME
```

#### Delete CloudWatch Log Groups

```bash
# List log groups
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda \
  --query "logGroups[*].logGroupName" \
  --output table

# Delete each log group
aws logs delete-log-group --log-group-name /aws/lambda/auth-handler
aws logs delete-log-group --log-group-name /aws/lambda/enroll-handler
aws logs delete-log-group --log-group-name /aws/lambda/identify-handler
aws logs delete-log-group --log-group-name /aws/lambda/people-handler
```

---

## Step 4: Verify Complete Cleanup

### Check CloudFormation

```bash
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE DELETE_FAILED \
  --query "StackSummaries[*].[StackName,StackStatus]" \
  --output table
```

Expected: No face-recognition related stacks

### Check Lambda

```bash
aws lambda list-functions --query "Functions[*].FunctionName"
```

Expected: No auth/enroll/identify/people handlers

### Check API Gateway

```bash
aws apigateway get-rest-apis
```

Expected: No face-recognition-api

### Check Cognito

```bash
aws cognito-idp list-user-pools --max-results 20
```

Expected: No face-recognition user pools

### Check S3

```bash
aws s3 ls | grep face
```

Expected: No face-recognition buckets

### Check DynamoDB

```bash
aws dynamodb list-tables
```

Expected: No face-recognition tables

### Check Resource Tags

```bash
# Find any remaining resources with project tag
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=face-recognition
```

Expected: Empty list

---

## Troubleshooting

### Stack Delete Failed

**Error**: `Stack cannot be deleted while in UPDATE_ROLLBACK_FAILED state`

**Solution**:
```bash
aws cloudformation continue-update-rollback --stack-name STACK_NAME
# Wait for rollback to complete, then delete again
aws cloudformation delete-stack --stack-name STACK_NAME
```

### Bucket Not Empty

**Error**: `The bucket you tried to delete is not empty`

**Solution**:
```bash
# Empty bucket first
aws s3 rm s3://bucket-name --recursive
# Then delete
aws s3 rb s3://bucket-name
```

### Resources Still Exist

If some resources remain after CloudFormation delete:
1. Manually delete orphaned resources (see Step 3B)
2. Check for resources in different regions
3. Use AWS Console to visually inspect

### Permission Denied

Ensure your AWS credentials have admin permissions:
```bash
aws sts get-caller-identity
# Should show your account ID

# Check permissions
aws iam get-user
```

---

## Cleanup Checklist

After cleanup, verify:

- [ ] No CloudFormation stacks exist
- [ ] No Lambda functions exist
- [ ] No API Gateways exist
- [ ] No Cognito User Pools exist
- [ ] No S3 buckets exist
- [ ] No DynamoDB tables exist
- [ ] No IAM roles for Lambda exist
- [ ] No CloudWatch log groups exist
- [ ] AWS billing shows no charges for these services

---

## Next Steps

After successful cleanup:
1. See `docs/AWS_INFRASTRUCTURE_DEPLOYMENT.md` for CDK deployment
2. See `docs/AWS_LAMBDA_DEPLOYMENT.md` for Lambda deployment
3. See `docs/AMPLIFY_DEPLOYMENT.md` for frontend deployment
