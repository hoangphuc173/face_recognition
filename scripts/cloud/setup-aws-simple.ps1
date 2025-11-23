# AWS Setup Script - Simple Version
# Tạo các resources cần thiết cho Face Recognition System

$ErrorActionPreference = "Continue"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AWS Face Recognition System Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$Region = "ap-southeast-1"

# Check AWS CLI
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✓ AWS CLI detected: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not found!" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host ""
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identityJson = aws sts get-caller-identity --output json 2>&1
    $identity = $identityJson | ConvertFrom-Json
    Write-Host "✓ Logged in as: $($identity.Arn)" -ForegroundColor Green
    Write-Host "  Account ID: $($identity.Account)" -ForegroundColor Gray
    $AccountId = $identity.Account
} catch {
    Write-Host "✗ Not logged in to AWS!" -ForegroundColor Red
    Write-Host "  Run: aws configure" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Creating AWS Resources..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Create S3 Bucket
Write-Host ""
Write-Host "1. Creating S3 Bucket..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$randomSuffix = Get-Random -Minimum 10000 -Maximum 99999
$BucketName = "face-recognition-$timestamp-$randomSuffix"

try {
    aws s3 mb s3://$BucketName --region $Region 2>&1
    Write-Host "   ✓ S3 Bucket created: $BucketName" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Error creating bucket" -ForegroundColor Yellow
}

# 2. Create Rekognition Collection
Write-Host ""
Write-Host "2. Creating Rekognition Collection..." -ForegroundColor Yellow
$CollectionId = "face-recognition-collection-dev"

try {
    aws rekognition create-collection --collection-id $CollectionId --region $Region 2>&1
    Write-Host "   ✓ Rekognition Collection created: $CollectionId" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Collection might already exist" -ForegroundColor Yellow
}

# 3. Create DynamoDB Tables
Write-Host ""
Write-Host "3. Creating DynamoDB Tables..." -ForegroundColor Yellow

# People Table
$tableName = "face-recognition-people-dev"
Write-Host "   Creating table: $tableName" -ForegroundColor Gray
try {
    aws dynamodb create-table `
        --table-name $tableName `
        --attribute-definitions AttributeName=person_id,AttributeType=S `
        --key-schema AttributeName=person_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $Region 2>&1 | Out-Null
    Write-Host "   ✓ Table $tableName created" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Table might already exist" -ForegroundColor Yellow
}

# Embeddings Table
$tableName = "face-recognition-embeddings-dev"
Write-Host "   Creating table: $tableName" -ForegroundColor Gray
try {
    aws dynamodb create-table `
        --table-name $tableName `
        --attribute-definitions AttributeName=embedding_id,AttributeType=S AttributeName=person_id,AttributeType=S `
        --key-schema AttributeName=embedding_id,KeyType=HASH `
        --global-secondary-indexes "IndexName=person_id-index,KeySchema=[{AttributeName=person_id,KeyType=HASH}],Projection={ProjectionType=ALL}" `
        --billing-mode PAY_PER_REQUEST `
        --region $Region 2>&1 | Out-Null
    Write-Host "   ✓ Table $tableName created" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Table might already exist" -ForegroundColor Yellow
}

# Matches Table
$tableName = "face-recognition-matches-dev"
Write-Host "   Creating table: $tableName" -ForegroundColor Gray
try {
    aws dynamodb create-table `
        --table-name $tableName `
        --attribute-definitions AttributeName=match_id,AttributeType=S AttributeName=person_id,AttributeType=S `
        --key-schema AttributeName=match_id,KeyType=HASH `
        --global-secondary-indexes "IndexName=person_id-index,KeySchema=[{AttributeName=person_id,KeyType=HASH}],Projection={ProjectionType=ALL}" `
        --billing-mode PAY_PER_REQUEST `
        --region $Region 2>&1 | Out-Null
    Write-Host "   ✓ Table $tableName created" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Table might already exist" -ForegroundColor Yellow
}

# 4. Save configuration
Write-Host ""
Write-Host "4. Saving configuration..." -ForegroundColor Yellow

$envContent = @"
# AWS Configuration
AWS_REGION=$Region
AWS_S3_BUCKET=$BucketName
AWS_REKOGNITION_COLLECTION=$CollectionId
AWS_ACCOUNT_ID=$AccountId

# DynamoDB Tables
AWS_DYNAMODB_PEOPLE_TABLE=face-recognition-people-dev
AWS_DYNAMODB_EMBEDDINGS_TABLE=face-recognition-embeddings-dev
AWS_DYNAMODB_MATCHES_TABLE=face-recognition-matches-dev

# App Settings
DEBUG=true
LOG_LEVEL=INFO
"@

$envPath = ".\aws\.env"
$envContent | Out-File -FilePath $envPath -Encoding UTF8 -Force
Write-Host "   ✓ Configuration saved to: $envPath" -ForegroundColor Green

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $Region" -ForegroundColor Gray
Write-Host "  S3 Bucket: $BucketName" -ForegroundColor Gray
Write-Host "  Rekognition Collection: $CollectionId" -ForegroundColor Gray
Write-Host "  Account ID: $AccountId" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Deploy Lambda: .\deploy-lambda-simple.ps1" -ForegroundColor Gray
Write-Host "  2. Or run local backend: cd aws && python -m uvicorn backend.api.app:app --reload --port 8888" -ForegroundColor Gray
Write-Host "  3. Start frontend: python app\gui_app.py" -ForegroundColor Gray
Write-Host ""
