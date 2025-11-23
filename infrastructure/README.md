# Face Recognition CDK Infrastructure

AWS CDK Infrastructure as Code for Serverless Face Recognition System with AI/ML.

## Prerequisites

- Node.js 18+ and npm
- AWS CLI configured with credentials
- AWS CDK CLI: `npm install -g aws-cdk`
- Docker (for SageMaker model deployment)

## Setup

```bash
# Install dependencies
npm install

# Bootstrap CDK (first time only)
npm run bootstrap

# Build TypeScript
npm run build
```

## Environment Configuration

Create `.env` file:

```env
AWS_ACCOUNT_ID=829717935400
AWS_REGION=ap-southeast-1
ENVIRONMENT=dev
PROJECT_NAME=face-recognition

# Optional: Custom domain
# API_DOMAIN_NAME=api.yourdomain.com
# CERTIFICATE_ARN=arn:aws:acm:...
```

## Deployment

```bash
# Deploy all stacks to dev
npm run deploy:dev

# Deploy all stacks to prod
npm run deploy:prod

# Deploy specific stack
cdk deploy FaceRecognitionStack-dev

# View changes before deploy
npm run diff

# Generate CloudFormation template
npm run synth
```

## Architecture

This CDK app deploys:

1. **Networking**: VPC, subnets, NAT gateway
2. **Storage**: S3 buckets, DynamoDB tables, ElastiCache Redis
3. **Compute**: Lambda functions (5 functions)
4. **AI/ML**: SageMaker serverless inference endpoint
5. **API**: API Gateway (REST + WebSocket)
6. **IoT**: IoT Core (things, policies, rules)
7. **Events**: EventBridge rules
8. **Monitoring**: CloudWatch dashboards, alarms, X-Ray
9. **Security**: IAM roles, KMS keys, Cognito user pool

## Stacks

- `FaceRecognitionStack-{env}` - Main infrastructure
- `FaceRecognitionCICDStack` - CI/CD pipeline (optional)

## Useful Commands

```bash
# List all stacks
cdk list

# Destroy all resources (careful!)
npm run destroy

# View specific stack template
cdk synth FaceRecognitionStack-dev

# Deploy with hotswap (faster for dev)
cdk deploy --hotswap

# Watch mode (auto-deploy on changes)
npm run watch
```

## Cost Estimation

Dev environment: ~$200/month
- SageMaker Serverless: $50
- Lambda: $10 (mostly free tier)
- API Gateway: $5
- DynamoDB: $10
- ElastiCache: $12
- S3: $5
- CloudWatch: $10
- Data transfer: $50
- Other services: $48

Production (10K requests/day): ~$500/month

## Testing

```bash
# Run CDK tests
npm test

# Validate CloudFormation templates
cdk synth --validate
```

## Security Notes

- All Lambda functions use least-privilege IAM roles
- S3 buckets have encryption at rest (SSE-S3)
- API Gateway uses Cognito authorizer
- VPC endpoints for AWS services (no internet gateway for Lambda)
- CloudWatch logs encrypted with KMS
- Secrets stored in AWS Secrets Manager

## Troubleshooting

**CDK bootstrap fails:**
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION --profile your-profile
```

**Lambda deployment fails:**
```bash
# Ensure Docker is running (for bundling)
docker ps
```

**Stack stuck in UPDATE_ROLLBACK_FAILED:**
```bash
# Continue rollback
aws cloudformation continue-update-rollback --stack-name STACK_NAME
```

## Support

For issues, contact: hoangphuc173
