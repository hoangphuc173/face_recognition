# AWS Setup Script - Tạo các resources cần thiết cho Face Recognition System
# Chạy: .\setup-aws.ps1

param(
    [string]$Region = "ap-southeast-1",
    [string]$BucketName = "",
    [string]$CollectionId = ""
)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  AWS Face Recognition System Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
try {
    $awsVersion = aws --version
    Write-Host "✓ AWS CLI detected: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not found! Please install: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host ""
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✓ Logged in as: $($identity.Arn)" -ForegroundColor Green
    Write-Host "  Account ID: $($identity.Account)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Not logged in to AWS!" -ForegroundColor Red
    Write-Host "  Run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Get bucket name if not provided
if ([string]::IsNullOrEmpty($BucketName)) {
    $BucketName = Read-Host "Enter S3 Bucket Name (e.g., my-face-recognition-bucket)"
}

# Get collection ID if not provided
if ([string]::IsNullOrEmpty($CollectionId)) {
    $CollectionId = Read-Host "Enter Rekognition Collection ID (e.g., my-face-collection)"
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Creating AWS Resources..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Create S3 Bucket
Write-Host ""
Write-Host "1. Creating S3 Bucket: $BucketName" -ForegroundColor Yellow
try {
    if ($Region -eq "us-east-1") {
        aws s3 mb s3://$BucketName 2>$null
    } else {
        aws s3 mb s3://$BucketName --region $Region 2>$null
    }
    Write-Host "   ✓ S3 Bucket created successfully" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Bucket might already exist or error occurred" -ForegroundColor Yellow
}

# 2. Enable S3 CORS
Write-Host ""
Write-Host "2. Configuring S3 CORS..." -ForegroundColor Yellow
$corsConfig = @"
{
    "CORSRules": [
        {
            "AllowedOrigins": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedHeaders": ["*"],
            "MaxAgeSeconds": 3000
        }
    ]
}
"@
$corsConfig | Out-File -FilePath "cors.json" -Encoding utf8
try {
    aws s3api put-bucket-cors --bucket $BucketName --cors-configuration file://cors.json
    Write-Host "   ✓ CORS configured" -ForegroundColor Green
    Remove-Item "cors.json"
} catch {
    Write-Host "   ⚠ CORS configuration failed" -ForegroundColor Yellow
}

# 3. Create Rekognition Collection
Write-Host ""
Write-Host "3. Creating Rekognition Collection: $CollectionId" -ForegroundColor Yellow
try {
    aws rekognition create-collection --collection-id $CollectionId --region $Region 2>$null
    Write-Host "   ✓ Rekognition Collection created" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Collection might already exist" -ForegroundColor Yellow
}

# 4. Create DynamoDB Tables
Write-Host ""
Write-Host "4. Creating DynamoDB Tables..." -ForegroundColor Yellow

# People Table
$tableName = "face-recognition-people-dev"
Write-Host "   Creating table: $tableName" -ForegroundColor Gray
try {
    aws dynamodb create-table `
        --table-name $tableName `
        --attribute-definitions AttributeName=person_id,AttributeType=S `
        --key-schema AttributeName=person_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $Region 2>$null
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
        --attribute-definitions AttributeName=face_id,AttributeType=S `
        --key-schema AttributeName=face_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $Region 2>$null
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
        --attribute-definitions AttributeName=match_id,AttributeType=S `
        --key-schema AttributeName=match_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $Region 2>$null
    Write-Host "   ✓ Table $tableName created" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Table might already exist" -ForegroundColor Yellow
}

# 5. Update .env file
Write-Host ""
Write-Host "5. Updating .env file..." -ForegroundColor Yellow
$envPath = ".\aws\.env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    $envContent = $envContent -replace "AWS_REGION=.*", "AWS_REGION=$Region"
    $envContent = $envContent -replace "AWS_S3_BUCKET=.*", "AWS_S3_BUCKET=$BucketName"
    $envContent = $envContent -replace "AWS_REKOGNITION_COLLECTION=.*", "AWS_REKOGNITION_COLLECTION=$CollectionId"
    $envContent = $envContent -replace "AWS_ACCOUNT_ID=.*", "AWS_ACCOUNT_ID=$($identity.Account)"
    $envContent | Out-File -FilePath $envPath -Encoding utf8
    Write-Host "   ✓ .env file updated" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $Region" -ForegroundColor Gray
Write-Host "  S3 Bucket: $BucketName" -ForegroundColor Gray
Write-Host "  Rekognition Collection: $CollectionId" -ForegroundColor Gray
Write-Host "  Account ID: $($identity.Account)" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Check .env file: aws\.env" -ForegroundColor Gray
Write-Host "  2. Start backend: python -m uvicorn backend.api.app:app --reload --port 8888" -ForegroundColor Gray
Write-Host "  3. Start GUI: python app/gui_app.py" -ForegroundColor Gray
Write-Host ""
