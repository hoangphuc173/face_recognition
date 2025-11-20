# Deploy Lambda Functions for Face Recognition System
# This script packages and deploys Lambda functions to AWS

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Deploying Lambda Functions to AWS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$REGION = "ap-southeast-1"
$LAMBDA_ROLE = "arn:aws:iam::829717935400:role/lambda-face-recognition-role"
$LAMBDA_RUNTIME = "python3.9"
$LAMBDA_TIMEOUT = 300
$LAMBDA_MEMORY = 512

# Environment variables for Lambda
$ENV_VARS = @{
    "AWS_REGION" = $REGION
    "AWS_REKOGNITION_COLLECTION" = "face-collection-demo"
    "AWS_S3_BUCKET" = "face-recognition-hoangphuc173"
    "PERSON_TABLE" = "face-recognition-people-dev"
    "FACES_TABLE" = "face-recognition-faces-dev"
    "EMBEDDINGS_TABLE" = "face-recognition-embeddings-dev"
    "MATCHES_TABLE" = "face-recognition-matches-dev"
    "CACHE_TABLE" = "face-recognition-match-history-dev"
    "TELEMETRY_TABLE" = "face-recognition-telemetry-dev"
}

$ENV_JSON = ($ENV_VARS | ConvertTo-Json -Compress)

# Step 1: Create IAM Role if not exists
Write-Host "Step 1: Checking IAM Role..." -ForegroundColor Yellow
$roleExists = aws iam get-role --role-name lambda-face-recognition-role 2>&1
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
    
    $trustPolicy | Out-File -FilePath "trust-policy.json" -Encoding UTF8
    
    aws iam create-role `
        --role-name lambda-face-recognition-role `
        --assume-role-policy-document file://trust-policy.json
    
    # Attach policies
    aws iam attach-role-policy `
        --role-name lambda-face-recognition-role `
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    aws iam attach-role-policy `
        --role-name lambda-face-recognition-role `
        --policy-arn arn:aws:iam::aws:policy/AmazonRekognitionFullAccess
    
    aws iam attach-role-policy `
        --role-name lambda-face-recognition-role `
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    
    aws iam attach-role-policy `
        --role-name lambda-face-recognition-role `
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
    
    Remove-Item trust-policy.json
    
    Write-Host "Waiting 10 seconds for role to propagate..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
} else {
    Write-Host "✅ IAM Role already exists" -ForegroundColor Green
}

# Step 2: Package and Deploy Identify Lambda
Write-Host "`nStep 2: Deploying Identify Lambda..." -ForegroundColor Yellow

Push-Location "aws\backend\lambda\functions\identify-handler"

# Create deployment package
if (Test-Path "package.zip") { Remove-Item "package.zip" }

# Install dependencies to package directory
pip install --target ./package boto3 pillow -q

# Copy Lambda code
Copy-Item "identify_handler.py" -Destination "package\lambda_function.py"

# Create zip
Compress-Archive -Path "package\*" -DestinationPath "package.zip"

# Deploy or update Lambda
$functionExists = aws lambda get-function --function-name face-identify-handler --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Lambda function..." -ForegroundColor Yellow
    aws lambda create-function `
        --function-name face-identify-handler `
        --runtime $LAMBDA_RUNTIME `
        --role $LAMBDA_ROLE `
        --handler lambda_function.lambda_handler `
        --zip-file fileb://package.zip `
        --timeout $LAMBDA_TIMEOUT `
        --memory-size $LAMBDA_MEMORY `
        --environment "Variables={$ENV_JSON}" `
        --region $REGION
} else {
    Write-Host "Updating Lambda function..." -ForegroundColor Yellow
    aws lambda update-function-code `
        --function-name face-identify-handler `
        --zip-file fileb://package.zip `
        --region $REGION
    
    aws lambda update-function-configuration `
        --function-name face-identify-handler `
        --environment "Variables={$ENV_JSON}" `
        --region $REGION
}

# Cleanup
Remove-Item -Recurse -Force package
Remove-Item package.zip

Pop-Location

Write-Host "✅ Identify Lambda deployed" -ForegroundColor Green

# Step 3: Create API Gateway
Write-Host "`nStep 3: Setting up API Gateway..." -ForegroundColor Yellow

# Check if API exists
$apiList = aws apigatewayv2 get-apis --region $REGION | ConvertFrom-Json
$existingApi = $apiList.Items | Where-Object { $_.Name -eq "face-recognition-api" }

if ($existingApi) {
    $API_ID = $existingApi.ApiId
    Write-Host "✅ API Gateway already exists: $API_ID" -ForegroundColor Green
} else {
    Write-Host "Creating API Gateway..." -ForegroundColor Yellow
    $apiResponse = aws apigatewayv2 create-api `
        --name face-recognition-api `
        --protocol-type HTTP `
        --region $REGION | ConvertFrom-Json
    
    $API_ID = $apiResponse.ApiId
    Write-Host "✅ Created API Gateway: $API_ID" -ForegroundColor Green
}

# Create integration
Write-Host "Creating Lambda integration..." -ForegroundColor Yellow

$LAMBDA_ARN = "arn:aws:lambda:${REGION}:829717935400:function:face-identify-handler"

$integrationResponse = aws apigatewayv2 create-integration `
    --api-id $API_ID `
    --integration-type AWS_PROXY `
    --integration-uri $LAMBDA_ARN `
    --payload-format-version "2.0" `
    --region $REGION | ConvertFrom-Json

$INTEGRATION_ID = $integrationResponse.IntegrationId

# Create route
aws apigatewayv2 create-route `
    --api-id $API_ID `
    --route-key "POST /identify" `
    --target "integrations/$INTEGRATION_ID" `
    --region $REGION

# Create stage
$stageExists = aws apigatewayv2 get-stages --api-id $API_ID --region $REGION 2>&1
if ($LASTEXITCODE -ne 0 -or !($stageExists | Select-String "prod")) {
    aws apigatewayv2 create-stage `
        --api-id $API_ID `
        --stage-name prod `
        --auto-deploy `
        --region $REGION
}

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission `
    --function-name face-identify-handler `
    --statement-id apigateway-invoke `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${REGION}:829717935400:${API_ID}/*/*" `
    --region $REGION 2>&1 | Out-Null

$API_ENDPOINT = "https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  ✅ Lambda Deployment Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "API Endpoint:" -ForegroundColor Cyan
Write-Host "  $API_ENDPOINT" -ForegroundColor White
Write-Host ""
Write-Host "Test with:" -ForegroundColor Cyan
Write-Host "  curl -X POST $API_ENDPOINT/identify -d '{""image_base64"":""...""}}'" -ForegroundColor White
Write-Host ""
