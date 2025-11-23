# Deploy Lambda Function - Simplified Version
# This script deploys a standalone Lambda function with minimal dependencies

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Deploying Lambda Function (Simplified)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$REGION = "ap-southeast-1"
$ACCOUNT_ID = "829717935400"
$LAMBDA_ROLE_NAME = "lambda-face-recognition-role"
$LAMBDA_ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/${LAMBDA_ROLE_NAME}"
$LAMBDA_FUNCTION_NAME = "face-identify-handler"
$LAMBDA_RUNTIME = "python3.11"
$LAMBDA_TIMEOUT = 30
$LAMBDA_MEMORY = 512

# Load config from .env file
if (Test-Path ".\aws\.env") {
    Write-Host "Loading configuration from .env..." -ForegroundColor Yellow
    $envContent = Get-Content ".\aws\.env"
    $S3_BUCKET = ($envContent | Select-String "AWS_S3_BUCKET=" | ForEach-Object { $_ -replace "AWS_S3_BUCKET=", "" }).Trim()
    $REKOGNITION_COLLECTION = ($envContent | Select-String "AWS_REKOGNITION_COLLECTION=" | ForEach-Object { $_ -replace "AWS_REKOGNITION_COLLECTION=", "" }).Trim()
    $PEOPLE_TABLE = ($envContent | Select-String "AWS_DYNAMODB_PEOPLE_TABLE=" | ForEach-Object { $_ -replace "AWS_DYNAMODB_PEOPLE_TABLE=", "" }).Trim()
    $MATCHES_TABLE = ($envContent | Select-String "AWS_DYNAMODB_MATCHES_TABLE=" | ForEach-Object { $_ -replace "AWS_DYNAMODB_MATCHES_TABLE=", "" }).Trim()
    
    Write-Host "  S3 Bucket: $S3_BUCKET" -ForegroundColor Gray
    Write-Host "  Rekognition: $REKOGNITION_COLLECTION" -ForegroundColor Gray
    Write-Host "  People Table: $PEOPLE_TABLE" -ForegroundColor Gray
}
else {
    Write-Host "Warning: .env file not found, using defaults" -ForegroundColor Yellow
    $S3_BUCKET = ""
    $REKOGNITION_COLLECTION = "face-recognition-collection-dev"
    $PEOPLE_TABLE = "face-recognition-people-dev"
    $MATCHES_TABLE = "face-recognition-matches-dev"
}

# Environment variables for Lambda
$ENV_VARS = @{
    "AWS_REGION"                 = $REGION
    "AWS_REKOGNITION_COLLECTION" = $REKOGNITION_COLLECTION
    "AWS_S3_BUCKET"              = $S3_BUCKET
    "PERSON_TABLE"               = $PEOPLE_TABLE
    "MATCHES_TABLE"              = $MATCHES_TABLE
    "LOG_LEVEL"                  = "INFO"
}

# Convert to JSON format for AWS CLI
$envVarsJson = ($ENV_VARS | ConvertTo-Json -Compress) -replace '"', '\"'

Write-Host ""
Write-Host "Step 1: Checking IAM Role..." -ForegroundColor Yellow
$roleExists = aws iam get-role --role-name $LAMBDA_ROLE_NAME 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating IAM Role..." -ForegroundColor Yellow
    
    $trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
    
    Set-Content -Path "trust-policy.json" -Value $trustPolicy -Encoding UTF8
    
    aws iam create-role `
        --role-name $LAMBDA_ROLE_NAME `
        --assume-role-policy-document file://trust-policy.json
    
    # Attach policies
    aws iam attach-role-policy `
        --role-name $LAMBDA_ROLE_NAME `
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    aws iam attach-role-policy `
        --role-name $LAMBDA_ROLE_NAME `
        --policy-arn arn:aws:iam::aws:policy/AmazonRekognitionFullAccess
    
    aws iam attach-role-policy `
        --role-name $LAMBDA_ROLE_NAME `
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    
    aws iam attach-role-policy `
        --role-name $LAMBDA_ROLE_NAME `
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
    
    Remove-Item trust-policy.json
    
    Write-Host "Waiting 15 seconds for role to propagate..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
}
else {
    Write-Host "✅ IAM Role already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 2: Packaging Lambda function..." -ForegroundColor Yellow

$lambdaDir = ".\aws\backend\lambda\functions\identify-handler"
Push-Location $lambdaDir

# Clean up old package
if (Test-Path "lambda-package.zip") { Remove-Item "lambda-package.zip" }

# Create zip with just the lambda function (boto3 is provided by AWS)
Compress-Archive -Path "lambda_function.py" -DestinationPath "lambda-package.zip" -Force

Write-Host "✅ Package created: lambda-package.zip" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Deploying Lambda function..." -ForegroundColor Yellow

# Check if function exists
$functionExists = aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $REGION 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating new Lambda function..." -ForegroundColor Yellow
    aws lambda create-function `
        --function-name $LAMBDA_FUNCTION_NAME `
        --runtime $LAMBDA_RUNTIME `
        --role $LAMBDA_ROLE_ARN `
        --handler lambda_function.lambda_handler `
        --zip-file fileb://lambda-package.zip `
        --timeout $LAMBDA_TIMEOUT `
        --memory-size $LAMBDA_MEMORY `
        --environment "Variables={AWS_REGION=$REGION,AWS_REKOGNITION_COLLECTION=$REKOGNITION_COLLECTION,AWS_S3_BUCKET=$S3_BUCKET,PERSON_TABLE=$PEOPLE_TABLE,MATCHES_TABLE=$MATCHES_TABLE,LOG_LEVEL=INFO}" `
        --region $REGION
}
else {
    Write-Host "Updating existing Lambda function..." -ForegroundColor Yellow
    
    # Update code
    aws lambda update-function-code `
        --function-name $LAMBDA_FUNCTION_NAME `
        --zip-file fileb://lambda-package.zip `
        --region $REGION | Out-Null
    
    # Update configuration
    aws lambda update-function-configuration `
        --function-name $LAMBDA_FUNCTION_NAME `
        --environment "Variables={AWS_REGION=$REGION,AWS_REKOGNITION_COLLECTION=$REKOGNITION_COLLECTION,AWS_S3_BUCKET=$S3_BUCKET,PERSON_TABLE=$PEOPLE_TABLE,MATCHES_TABLE=$MATCHES_TABLE,LOG_LEVEL=INFO}" `
        --timeout $LAMBDA_TIMEOUT `
        --memory-size $LAMBDA_MEMORY `
        --region $REGION | Out-Null
}

# Cleanup
Remove-Item lambda-package.zip

Pop-Location

Write-Host "✅ Lambda function deployed successfully" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Setting up API Gateway..." -ForegroundColor Yellow

# Check if API exists
$apiList = aws apigatewayv2 get-apis --region $REGION | ConvertFrom-Json
$existingApi = $apiList.Items | Where-Object { $_.Name -eq "face-recognition-api" }

if ($existingApi) {
    $API_ID = $existingApi.ApiId
    Write-Host "✅ API Gateway already exists: $API_ID" -ForegroundColor Green
}
else {
    Write-Host "Creating API Gateway..." -ForegroundColor Yellow
    $apiResponse = aws apigatewayv2 create-api `
        --name face-recognition-api `
        --protocol-type HTTP `
        --cors-configuration "AllowOrigins=*,AllowMethods=*,AllowHeaders=*" `
        --region $REGION | ConvertFrom-Json
    
    $API_ID = $apiResponse.ApiId
    Write-Host "✅ Created API Gateway: $API_ID" -ForegroundColor Green
}

# Create Lambda integration
$LAMBDA_ARN = "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_FUNCTION_NAME}"

Write-Host "Creating integration for /identify endpoint..." -ForegroundColor Yellow

$integrationResponse = aws apigatewayv2 create-integration `
    --api-id $API_ID `
    --integration-type AWS_PROXY `
    --integration-uri $LAMBDA_ARN `
    --payload-format-version "2.0" `
    --region $REGION 2>$null | ConvertFrom-Json

if ($integrationResponse) {
    $INTEGRATION_ID = $integrationResponse.IntegrationId
    
    # Create route
    aws apigatewayv2 create-route `
        --api-id $API_ID `
        --route-key "POST /identify" `
        --target "integrations/$INTEGRATION_ID" `
        --region $REGION 2>$null | Out-Null
    
    Write-Host "✅ Route created: POST /identify" -ForegroundColor Green
}

# Create or update stage
aws apigatewayv2 create-stage `
    --api-id $API_ID `
    --stage-name prod `
    --auto-deploy `
    --region $REGION 2>$null | Out-Null

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission `
    --function-name $LAMBDA_FUNCTION_NAME `
    --statement-id apigateway-invoke-$(Get-Random) `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/*" `
    --region $REGION 2>$null | Out-Null

$API_ENDPOINT = "https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  ✅ Deployment Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📌 API Endpoint:" -ForegroundColor Cyan
Write-Host "  $API_ENDPOINT" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test with:" -ForegroundColor Cyan
Write-Host "  curl -X POST $API_ENDPOINT/identify -H 'Content-Type: application/json' -d '{""image_base64"":""...""}'" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Update frontend to use this API endpoint" -ForegroundColor Gray
Write-Host "  2. Deploy enroll Lambda function (optional)" -ForegroundColor Gray
Write-Host "  3. Test the system end-to-end" -ForegroundColor Gray
Write-Host ""
