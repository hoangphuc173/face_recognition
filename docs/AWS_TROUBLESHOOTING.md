# AWS Troubleshooting Guide

Common issues và solutions cho Face Recognition system deployment.

---

## Deployment Issues

### CDK Bootstrap Failed

**Error**: `Unable to resolve AWS account`

**Solution**:
```bash
# Configure AWS CLI
aws configure
# Enter: Access Key, Secret Key, Region

# Verify
aws sts get-caller-identity
```

---

**Error**: `Need to perform AWS calls for account XXX, but no credentials configured`

**Solution**:
```bash
# Export credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Or use AWS profile
aws configure --profile myprofile
export AWS_PROFILE=myprofile
```

---

### CloudFormation Stack Stuck

**Error**: `Stack is in UPDATE_ROLLBACK_FAILED state`

**Solution**:
```bash
# Continue rollback
aws cloudformation continue-update-rollback \
  --stack-name FaceRecognitionStack-prod

# Wait for completion
aws cloudformation wait stack-rollback-complete \
  --stack-name FaceRecognitionStack-prod

# Then delete
aws cloudformation delete-stack \
  --stack-name FaceRecognitionStack-prod
```

---

**Error**: `Stack deletion stuck`

**Solution**:
```bash
# Check stack events
aws cloudformation describe-stack-events \
  --stack-name FaceRecognitionStack-prod \
  --max-items 10

# If specific resource failed, delete manually then retry stack deletion
```

---

### Lambda Deployment Failed

**Error**: `InvalidParameterValueException: Unzipped size must be smaller than 262144000 bytes`

**Solution**: Your Lambda package or layer is too large.

```bash
# Check layer size
ls -lh backend/layer.zip

# If > 250MB, optimize dependencies:
pip install -r requirements.txt -t layer/python/ --no-deps
# Then add missing deps one by one
```

---

**Error**: `ResourceConflictException: Function already exists`

**Solution**:
```bash
# Delete existing function first
aws lambda delete-function --function-name auth-handler

# Then redeploy
aws lambda create-function ...
```

---

## Runtime Issues

### Lambda Timeout

**Error**: `Task timed out after 30.00 seconds`

**Solution**:
```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name enroll-handler \
  --timeout 60

# Or in CDK code:
# timeout: cdk.Duration.seconds(60)
```

---

### Lambda Out of Memory

**Error**: `Process exited after running out of memory`

**Solution**:
```bash
# Increase memory
aws lambda update-function-configuration \
  --function-name identify-handler \
  --memory-size 1024

# Monitor memory usage
aws lambda get-function-configuration \
  --function-name identify-handler \
  --query 'MemorySize'
```

---

### Module Not Found

**Error**: `Unable to import module 'main': No module named 'fastapi'`

**Solution**: Layer not attached or incorrect.

```bash
# Check layer
aws lambda get-function-configuration \
  --function-name auth-handler \
  --query 'Layers'

# If no layer, add it
aws lambda update-function-configuration \
  --function-name auth-handler \
  --layers $LAYER_ARN

# If layer exists, rebuild it
scripts\utilities\build-layer.ps1
# Then update layer version
```

---

### Permission Denied

**Error**: `User is not authorized to perform: lambda:InvokeFunction`

**Solution**:
```bash
# Add permission for API Gateway to invoke Lambda
aws lambda add-permission \
  --function-name auth-handler \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:REGION:ACCOUNT:API_ID/*/*"
```

---

## API Gateway Issues

### CORS Errors

**Error**: `No 'Access-Control-Allow-Origin' header is present`

**Solution**:
```bash
# Enable CORS for resource
aws apigateway update-integration-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --status-code 200 \
  --patch-operations \
    op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value="'*'"
```

Or in Lambda response:
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

**Error**: `{"message": "Internal server error"}`

**Possible causes**:
1. Lambda timeout
2. Lambda function error
3. Invalid Lambda response format

**Solution**:
```bash
# Check Lambda logs
aws logs tail /aws/lambda/auth-handler --since 10m

# Check Lambda response format (must be proxy format)
{
  "statusCode": 200,
  "headers": {...},
  "body": "..." # Must be string, not object!
}
```

---

### 403 Forbidden

**Error**: `User is not authorized to access this resource`

**Solution**: Check Cognito authorizer configuration.

```bash
# Verify authorizer is configured
aws apigateway get-authorizers --rest-api-id $API_ID

# Test with valid JWT token
curl -H "Authorization: Bearer $JWT_TOKEN" $API_URL/people
```

---

## Cognito Issues

### User Not Confirmed

**Error**: `User is not confirmed`

**Solution**:
```bash
# Confirm user manually
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com

# Or set auto-confirm in user pool settings
```

---

### Invalid Password

**Error**: `Password does not conform to policy`

**Solution**: Password must meet requirements:
- Minimum 8 characters
- At least 1 uppercase
- At least 1 lowercase
- At least 1 number
- At least 1 special character

---

### Too Many Requests

**Error**: `TooManyRequestsException: Rate exceeded`

**Solution**: Cognito has rate limits. Wait and retry, or request limit increase.

---

## S3 Issues

### Access Denied

**Error**: `Access Denied` when uploading to S3

**Solution**:
```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket $BUCKET_NAME

# Check Lambda role has S3 permissions
aws iam get-role-policy \
  --role-name lambda-execution-role \
  --policy-name S3Access
  
# Add S3 permissions to Lambda role if missing
```

---

### Bucket Not Empty

**Error**: `The bucket you tried to delete is not empty`

**Solution**:
```bash
# Empty bucket first
aws s3 rm s3://$BUCKET_NAME --recursive

# Then delete
aws s3 rb s3://$BUCKET_NAME
```

---

## DynamoDB Issues

### Item Not Found

**Error**: `Item does not exist`

**Solution**:
```bash
# Verify table exists
aws dynamodb describe-table --table-name face-recognition-users

# Scan table
aws dynamodb scan --table-name face-recognition-users

# Check partition key format
```

---

### ProvisionedThroughputExceededException

**Error**: `The level of configured provisioned throughput for the table was exceeded`

**Solution**:
```bash
# Switch to on-demand billing
aws dynamodb update-table \
  --table-name face-recognition-users \
  --billing-mode PAY_PER_REQUEST

# Or increase provisioned capacity
aws dynamodb update-table \
  --table-name face-recognition-users \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10
```

---

## Rekognition Issues

### Face Not Detected

**Error**: `InvalidParameterException: There are no faces in the image`

**Solution**:
- Image quality too low
- Face too small (< 100x100 pixels)
- Face at angle (> 30° pitch/roll/yaw)
- Poor lighting
- Face occluded

**Improve image**:
- Good lighting
- Face centered
- Face looking at camera
- Minimum 640x480 resolution

---

### Collection Not Found

**Error**: `ResourceNotFoundException: Collection id: face-recognition-collection not found`

**Solution**:
```bash
# Create collection
aws rekognition create-collection \
  --collection-id face-recognition-collection

# Verify
aws rekognition describe-collection \
  --collection-id face-recognition-collection
```

---

## Amplify Issues

### Build Failed

**Error**: `Build failed`

**Solution**:
```bash
# Check build logs in Amplify Console

# Common causes:
# 1. Missing environment variables
# 2. Node version mismatch
# 3. Build command incorrect
# 4. Out of memory
```

Fix in `amplify.yml`:
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

### Environment Variables Not Working

**Error**: API calls go to localhost instead of production API

**Solution**:
```bash
# In Amplify Console:
# 1. Go to Environment variables
# 2. Add: NEXT_PUBLIC_API_URL=https://API_ID.execute-api.us-east-1.amazonaws.com/prod
# 3. Redeploy

# Verify in browser console:
console.log(process.env.NEXT_PUBLIC_API_URL)
```

---

## General Debugging

### Enable Detailed Logging

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

### Check CloudWatch Logs

```bash
# Tail logs
aws logs tail /aws/lambda/auth-handler --follow

# Filter logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/auth-handler \
  --filter-pattern "ERROR"

# Get specific time range
aws logs filter-log-events \
  --log-group-name /aws/lambda/auth-handler \
  --start-time $(date -d '1 hour ago' +%s)000
```

---

## Getting Help

If still stuck:

1. **Check CloudWatch Logs**: Most detailed error information
2. **Check AWS Service Health**: https://status.aws.amazon.com
3. **Review IAM Permissions**: Ensure roles have required permissions
4. **Test Locally**: Use local development to isolate issues
5. **AWS Support**: Create support ticket if needed

---

## Quick Diagnostic Script

```bash
#!/bin/bash
# diagnose.sh - Quick health check

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

echo "=== Recent Lambda Errors ==="
aws logs filter-log-events \
  --log-group-name /aws/lambda/auth-handler \
  --filter-pattern "ERROR" \
  --max-items 5
```

Run: `chmod +x diagnose.sh && ./diagnose.sh`
