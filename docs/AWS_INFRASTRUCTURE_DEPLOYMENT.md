# AWS Infrastructure Deployment (CDK)

Hướng dẫn deploy AWS infrastructure sử dụng AWS CDK.

---

## Prerequisites

- **Node.js 18+** and npm
- **AWS CLI** configured: `aws configure`
- **AWS CDK CLI**: `npm install -g aws-cdk`
- **Admin permissions** trong AWS account
- **Docker** (for Lambda bundling - optional)

---

## Step 1: Setup CDK Project

### Install Dependencies

```bash
cd infrastructure
npm install
```

### Configure Environment

Create `.env` file:

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

**Get your AWS Account ID**:
```bash
aws sts get-caller-identity --query Account --output text
```

---

## Step 2: Bootstrap CDK

Bootstrap CDK trong account (chỉ cần 1 lần):

```bash
cd infrastructure

# Bootstrap
cdk bootstrap

# Or với explicit account/region
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

This creates:
- S3 bucket for CDK assets
- ECR repository for Docker images
- IAM roles for deployments
- CloudFormation stack: `CDKToolkit`

**Verify bootstrap**:
```bash
aws cloudformation describe-stacks --stack-name CDKToolkit
```

---

## Step 3: Review Infrastructure Code

### Check Main Stack

```bash
# View infrastructure code
code infrastructure/lib/main-stack.ts

# Or read with cat/type
cat infrastructure/lib/main-stack.ts
```

**Resources created by CDK**:
- ✅ Cognito User Pool + Client
- ✅ S3 Bucket (encrypted with KMS)
- ✅ DynamoDB Table (encrypted)
- ✅ Rekognition Face Collection
- ✅ IAM Roles for Lambda
- ✅ KMS Keys
- ✅ API Gateway (basic setup)

### Build TypeScript

```bash
cd infrastructure
npm run build
```

---

## Step 4: Preview Changes

```bash
cd infrastructure

# Show what will be created
cdk diff

# Generate CloudFormation template
cdk synth

# View template
cdk synth > template.yaml
code template.yaml
```

---

## Step 5: Deploy Infrastructure

### Option A: Deploy All Stacks

```bash
cd infrastructure

# Deploy without approval prompts
cdk deploy --all --require-approval never

# Or deploy with review
cdk deploy --all
```

### Option B: Deploy Specific Stack

```bash
# Deploy main stack only
cdk deploy FaceRecognitionStack-prod

# Deploy with parameters
cdk deploy FaceRecognitionStack-prod \
  --parameters environment=prod \
  --parameters projectName=face-recognition
```

**Wait for deployment** (5-10 minutes)

---

## Step 6: Capture Outputs

After deployment, capture important outputs:

```bash
# Get all outputs
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs' \
  > infrastructure/outputs.json

# View outputs
cat infrastructure/outputs.json
```

**Important outputs**:
- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito Client ID  
- `S3BucketName`: S3 bucket for images
- `DynamoDBTableName`: DynamoDB table name
- `RekognitionCollectionId`: Rekognition collection ID
- `ApiGatewayUrl`: API Gateway endpoint (after Lambda deployment)

**Save these values** - you'll need them for Lambda and frontend configuration!

---

## Step 7: Verify Infrastructure

### Verify CloudFormation Stack

```bash
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].StackStatus'
```

Expected: `CREATE_COMPLETE` or `UPDATE_COMPLETE`

### Verify Cognito User Pool

```bash
# Get outputs
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Describe user pool
aws cognito-idp describe-user-pool --user-pool-id $USER_POOL_ID
```

### Verify S3 Bucket

```bash
# Get bucket name
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# List bucket (should be empty)
aws s3 ls s3://$BUCKET_NAME

# Check encryption
aws s3api get-bucket-encryption --bucket $BUCKET_NAME
```

### Verify DynamoDB Table

```bash
# Get table name
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DynamoDBTableName`].OutputValue' \
  --output text)

# Describe table
aws dynamodb describe-table --table-name $TABLE_NAME

# Scan table (should be empty)
aws dynamodb scan --table-name $TABLE_NAME
```

### Verify Rekognition Collection

```bash
# List collections
aws rekognition list-collections

# Describe collection
aws rekognition describe-collection --collection-id face-recognition-collection
```

---

## Step 8: Create Cognito Groups

Create user groups for RBAC:

```bash
# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create Admin group
aws cognito-idp create-group \
  --user-pool-id $USER_POOL_ID \
  --group-name Admin \
  --description "Administrator group with full permissions"

# Create Staff group
aws cognito-idp create-group \
  --user-pool-id $USER_POOL_ID \
  --group-name Staff \
  --description "Staff group with limited permissions"

# Create Guest group
aws cognito-idp create-group \
  --user-pool-id $USER_POOL_ID \
  --group-name Guest \
  --description "Guest group with read-only permissions"

# Verify groups
aws cognito-idp list-groups --user-pool-id $USER_POOL_ID
```

---

## Monitoring & Logs

### CloudWatch Dashboard

CDK creates CloudWatch dashboard:

```bash
# List dashboards
aws cloudwatch list-dashboards

# View in console
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:
```

### CloudWatch Logs

```bash
# List log groups created
aws logs describe-log-groups \
  --log-group-name-prefix /aws/face-recognition
```

---

## Cost Estimation

**Monthly costs** for infrastructure only (no traffic):

| Service | Cost |
|---------|------|
| Cognito User Pool | $0 (50K MAU free) |
| S3 Bucket | ~$1 (5GB free) |
| DynamoDB | ~$2.50 (25GB free) |
| Rekognition Collection | $0 (no charges when not used) |
| CloudWatch Logs | ~$0.50 |
| KMS Keys | $1/key/month |
| **Total** | **~$5-10/month** |

**With traffic** (1000 requests/day):
- Lambda: ~$10
- API Gateway: ~$3.50
- Rekognition: ~$1 (1000 faces)
- Data transfer: ~$5
- **Total**: **~$25-30/month**

---

## Update Infrastructure

To update infrastructure after code changes:

```bash
cd infrastructure

# Build
npm run build

# Preview changes
cdk diff

# Deploy updates
cdk deploy --all
```

---

## Rollback

If deployment fails:

```bash
# CloudFormation auto-rolls back on failure
# Check status
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod

# If stuck, continue rollback
aws cloudformation continue-update-rollback \
  --stack-name FaceRecognitionStack-prod
```

---

## Troubleshooting

### "Unable to resolve AWS account"

**Solution**: Configure AWS CLI
```bash
aws configure
# Enter your access key, secret key, region
```

### "CDK bootstrap required"

**Solution**: Bootstrap CDK
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### "Insufficient permissions"

**Solution**: Ensure IAM user has:
- CloudFormationFullAccess
- IAMFullAccess
- S3FullAccess
- DynamoDBFullAccess
- CognitoIdpFullAccess
- RekognitionFullAccess

### "Stack already exists"

If re-deploying after cleanup:
```bash
# Wait for previous stack deletion
aws cloudformation wait stack-delete-complete \
  --stack-name FaceRecognitionStack-prod

# Then deploy again
cdk deploy
```

---

## Next Steps

After successful infrastructure deployment:

1. ✅ **Save outputs** to `infrastructure/outputs.json`
2. 📋 **Deploy Lambda functions**: See `docs/AWS_LAMBDA_DEPLOYMENT.md`
3. 🚀 **Deploy frontend**: See `docs/AMPLIFY_DEPLOYMENT.md`
4. 👤 **Create users**: See `docs/AWS_TESTING_GUIDE.md`

---

## Clean Up

To delete all infrastructure:

```bash
cd infrastructure
cdk destroy --all

# Confirm deletion when prompted
```

See `docs/AWS_CLEANUP_GUIDE.md` for detailed cleanup instructions.
