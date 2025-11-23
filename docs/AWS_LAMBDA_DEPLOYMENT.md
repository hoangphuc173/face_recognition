# AWS Lambda Deployment Guide

Hướng dẫn deploy Lambda functions cho Face Recognition system.

---

## Prerequisites

- ✅ Infrastructure deployed (Cognito, S3, DynamoDB)
- AWS CLI configured
- Python 3.11+
- PowerShell (for build scripts)

---

## Architecture

**4 Lambda Functions**:
1. **auth-handler**: User registration, login, verification
2. **enroll-handler**: Face enrollment with Rekognition
3. **identify-handler**: Face identification
4. **people-handler**: User CRUD operations

---

## Step 1: Build Lambda Layer

Lambda Layer chứa Python dependencies (FastAPI, Pillow, boto3, etc.)

### Using Build Script

```bash
# Windows
scripts\utilities\build-layer.ps1

# Linux/Mac
chmod +x scripts/utilities/build-layer.sh
scripts/utilities/build-layer.sh
```

This creates `backend/layer.zip` (~50MB)

### Manual Build (if script fails)

```bash
cd backend

# Create layer directory
mkdir -p layer/python

# Install dependencies
pip install -r requirements.txt -t layer/python/

# Zip layer
cd layer
zip -r ../layer.zip python/
cd ..
```

### Upload Layer to AWS

```bash
# Upload layer
aws lambda publish-layer-version \
  --layer-name python-deps \
  --description "Python dependencies for face recognition" \
  --zip-file fileb://backend/layer.zip \
  --compatible-runtimes python3.11

# Save layer ARN
LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name python-deps \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

echo $LAYER_ARN
```

---

## Step 2: Get Infrastructure Outputs

Get values from CDK deployment:

```bash
# Get Cognito User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Get Cognito Client ID  
CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text)

# Get S3 Bucket
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Get DynamoDB Table
DYNAMODB_TABLE=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DynamoDBTableName`].OutputValue' \
  --output text)

# Get Rekognition Collection
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

## Step 3: Deploy Auth Handler

### Package Function

```bash
cd backend/src/auth
zip -r auth-handler.zip .
cd ../../..
```

### Create Lambda Function

```bash
# Get IAM Role ARN from CDK outputs
ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaExecutionRoleArn`].OutputValue' \
  --output text)

# Create function
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

## Step 4: Deploy Enroll Handler

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

## Step 5: Deploy Identify Handler

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

## Step 6: Deploy People Handler

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

## Step 7: Setup API Gateway

### Create API

```bash
# Create REST API
API_ID=$(aws apigateway create-rest-api \
  --name face-recognition-api \
  --description "Face Recognition API" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' \
  --output text)

# Get root resource
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' \
  --output text)
```

### Create Auth Resource

```bash
# Create /auth resource
AUTH_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part auth \
  --query 'id' \
  --output text)

# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $AUTH_RESOURCE \
  --http-method POST \
  --authorization-type NONE

# Integrate with Lambda
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $AUTH_RESOURCE \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$(aws lambda get-function --function-name auth-handler --query 'Configuration.FunctionArn' --output text)/invocations

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name auth-handler \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*"
```

### Deploy API

```bash
# Deploy to prod stage
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod

# Get API URL
API_URL="https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"
echo "API Gateway URL: $API_URL"
```

---

## Step 8: Test Lambda Functions

### Test Auth Handler

```bash
# Invoke directly
aws lambda invoke \
  --function-name auth-handler \
  --payload '{"action":"health"}' \
  response.json

cat response.json
```

### Test via API Gateway

```bash
# Test registration
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

---

## Step 9: Enable CloudWatch Logs

```bash
# Update logging for each function
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

## Update Lambda Functions

To update function code:

```bash
# Repackage
cd backend/src/auth
zip -r auth-handler.zip .

# Update function
aws lambda update-function-code \
  --function-name auth-handler \
  --zip-file fileb://auth-handler.zip
```

---

## Monitoring

### View Logs

```bash
# Tail logs
aws logs tail /aws/lambda/auth-handler --follow
```

### View Metrics

```bash
# Get invocation count
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

## Troubleshooting

### "Task timed out after 30.00 seconds"

Increase timeout:
```bash
aws lambda update-function-configuration \
  --function-name FUNCTION_NAME \
  --timeout 60
```

### "Runtime exited with error: exit status 1"

Check logs:
```bash
aws logs tail /aws/lambda/FUNCTION_NAME --since 10m
```

### Module not found errors

Verify layer is attached:
```bash
aws lambda get-function-configuration \
  --function-name FUNCTION_NAME \
  --query 'Layers'
```

---

## Next Steps

After Lambda deployment:

1. ✅ Save API Gateway URL
2. 🚀 Deploy frontend with API URL: See `docs/AMPLIFY_DEPLOYMENT.md`
3. 🧪 Test end-to-end: See `docs/AWS_TESTING_GUIDE.md`
