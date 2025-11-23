# Cloud/Production Environment

## AWS Amplify Environment Variables

Set these in Amplify Console under "Environment variables":

```bash
# Required: API Gateway URL
NEXT_PUBLIC_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

### How to Get API Gateway URL

1. Open AWS Console → API Gateway
2. Click your API (e.g., "face-recognition-api")
3. Go to **Stages** → **prod**
4. Copy the **Invoke URL**

## Lambda Environment Variables

Lambda functions get their environment variables from:
- AWS Systems Manager Parameter Store
- AWS Secrets Manager
- Environment variables set in Lambda console

### Required for Lambda Functions

```bash
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
S3_BUCKET_NAME=your-production-bucket
DYNAMODB_TABLE_NAME=face-recognition-users
REGION=us-east-1
```

These are set automatically by the CDK infrastructure deployment.

## Deployment

See `docs/CLOUD_DEPLOYMENT.md` for full deployment guide.
