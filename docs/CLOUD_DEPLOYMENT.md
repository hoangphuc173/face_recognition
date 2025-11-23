# Cloud Deployment Guide

Hướng dẫn deploy hệ thống lên AWS Cloud.

---

## Architecture Overview

```
User → Amplify (Frontend) → API Gateway → Lambda Functions → AWS Services
                                              ├─→ Cognito (Auth)
                                              ├─→ Rekognition (Face Recognition)
                                              ├─→ S3 (Image Storage)
                                              └─→ DynamoDB (User Data)
```

---

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.11+
- Node.js 18+
- AWS CDK (for infrastructure deployment)

---

## Deployment Steps

### Step 1: AWS Infrastructure Setup

Deploy AWS resources using CDK:

```bash
# Install dependencies
cd infrastructure
npm install

# Bootstrap CDK (first time only)
npx aws-cdk bootstrap

# Deploy infrastructure
npx aws-cdk deploy
```

This creates:
- Cognito User Pool
- S3 Bucket
- DynamoDB Table
- IAM Roles

Or use the setup script:
```bash
scripts\cloud\setup-aws.ps1
```

### Step 2: Deploy Lambda Functions

Build and deploy Lambda functions:

```bash
scripts\cloud\deploy-lambda-quick.ps1
```

This will:
1. Build Python dependencies layer
2. Package Lambda functions
3. Deploy to AWS Lambda
4. Create/update API Gateway

**Functions deployed**:
- `auth-handler`: Authentication (register, login, verify)
- `enroll-handler`: Face enrollment
- `identify-handler`: Face identification
- `people-handler`: User management

### Step 3: Deploy Frontend to Amplify

See `AMPLIFY_DEPLOYMENT.md` for detailed Amplify deployment.

Quick version:
```bash
scripts\deployment\deploy-frontend.bat
```

### Step 4: Configure Environment Variables

#### In Amplify Console

Navigate to: Amplify Console → Your App → Environment variables

Add:
```
NEXT_PUBLIC_API_URL = https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

Get API URL from API Gateway console.

---

## Testing Cloud Deployment

### Test Lambda Functions

Use AWS Console test feature or:

```bash
# Test auth
aws lambda invoke --function-name auth-handler --payload file://test-event.json response.json

# Test enroll
aws lambda invoke --function-name enroll-handler --payload file://test-enroll.json response.json
```

### Test Frontend

Open Amplify deployment URL:
```
https://[branch].[app-id].amplifyapp.com
```

Test complete flow:
1. Register → Verify email → Login
2. Enroll face
3. Identify face

---

## Monitoring & Logs

### CloudWatch Logs

View logs for each Lambda function:
```bash
aws logs tail /aws/lambda/auth-handler --follow
aws logs tail /aws/lambda/enroll-handler --follow
aws logs tail /aws/lambda/identify-handler --follow
```

### Amplify Build Logs

Check build logs in Amplify Console:
- Amplify Console → Your App → Deployments
- Click on build to see logs

---

## Updating Deployment

### Update Lambda Functions

```bash
scripts\cloud\deploy-lambda-quick.ps1
```

### Update Frontend

Push to GitHub → Amplify auto-deploys (if auto-deploy enabled).

Or manually trigger in Amplify Console.

### Update Infrastructure

```bash
cd infrastructure
npx aws-cdk deploy
```

---

## Cost Optimization

### Free Tier Eligible

- Lambda: 1M requests/month
- API Gateway: 1M requests/month
- Cognito: 50,000 MAUs
- S3: 5GB storage
- DynamoDB: 25GB storage

### Cost Estimates (Beyond Free Tier)

- Lambda: ~$0.20 per 1M requests
- Rekognition: $0.001 per image processed
- API Gateway: $3.50 per 1M requests
- S3: $0.023 per GB/month

---

## Security Best Practices

1. **Use Least Privilege IAM Roles**
   - Lambda functions have minimal required permissions

2. **Enable CloudWatch Logging**
   - All functions log to CloudWatch

3. **Use Cognito for Authentication**
   - Don't store passwords in DynamoDB
   - Use JWT tokens

4. **Encrypt Data**
   - S3 bucket has encryption enabled
   - DynamoDB has encryption at rest

---

## Troubleshooting

### Lambda Function Errors

Check CloudWatch logs:
```bash
aws logs tail /aws/lambda/[function-name] --follow
```

### API Gateway 502 Errors

- Check Lambda function timeout (increase if needed)
- Verify Lambda permissions
- Check function logs for errors

### Amplify Build Failures

- Check build logs in Amplify Console
- Verify environment variables are set
- Check `amplify.yml` configuration

---

## Rollback

### Lambda Functions

Deploy previous version:
```bash
aws lambda update-function-code --function-name [name] --s3-bucket [bucket] --s3-key [old-key]
```

### Frontend

Amplify Console → Deployments → Select previous deployment → Redeploy

---

## Next Steps

- Setup CloudWatch alarms for monitoring
- Configure custom domain in Amplify
- Setup CI/CD pipeline
- Review security settings
