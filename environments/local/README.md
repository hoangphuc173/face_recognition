# Local Development Environment

## Backend Environment Variables

Create a `.env.local` file in the root directory with:

```bash
# AWS Credentials (for local testing with AWS services)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Cognito Configuration
COGNITO_USER_POOL_ID=your_user_pool_id
COGNITO_CLIENT_ID=your_client_id

# S3 Bucket
S3_BUCKET_NAME=your_bucket_name

# DynamoDB Table
DYNAMODB_TABLE_NAME=your_table_name

# Local Development
LOCAL_MODE=true
DEBUG=true
```

## Frontend Environment Variables

Create `.env.local` in `frontend/web/`:

```bash
# Local backend API
NEXT_PUBLIC_API_URL=http://localhost:5555
```

For desktop app, the API URL is configured in the app settings.

## Quick Start

1. Copy this file to root: `.env.local`
2. Fill in your AWS credentials
3. Run local backend: `scripts\local\backend\start-backend-only.bat`
4. Run frontend: `scripts\local\frontend\start-frontend.bat`
