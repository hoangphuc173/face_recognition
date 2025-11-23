# Quick Deploy Lambda - Auto detect Account ID
$ErrorActionPreference = "Continue"

Write-Host "`n🚀 DEPLOYING LAMBDA FUNCTION" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

# Auto-detect Account ID
$identity = aws sts get-caller-identity | ConvertFrom-Json
$ACCOUNT_ID = $identity.Account
$REGION = "ap-southeast-1"

Write-Host "`n📌 Configuration:" -ForegroundColor Yellow
Write-Host "  Account: $ACCOUNT_ID"
Write-Host "  Region: $REGION"

# Load AWS config from .env
if (Test-Path ".\aws\.env") {
    $envLines = Get-Content ".\aws\.env"
    $S3_BUCKET = ($envLines | Select-String "^AWS_S3_BUCKET=" | ForEach-Object { ($_ -replace "AWS_S3_BUCKET=", "").Trim() }) | Select-Object -First 1
    $COLLECTION = ($envLines | Select-String "^AWS_REKOGNITION_COLLECTION=" | ForEach-Object { ($_ -replace "AWS_REKOGNITION_COLLECTION=", "").Trim() }) | Select-Object -First 1
    $PEOPLE_TABLE = ($envLines | Select-String "^AWS_DYNAMODB_PEOPLE_TABLE=" | ForEach-Object { ($_ -replace "AWS_DYNAMODB_PEOPLE_TABLE=", "").Trim() }) | Select-Object -First 1
    $MATCHES_TABLE = ($envLines | Select-String "^AWS_DYNAMODB_MATCHES_TABLE=" | ForEach-Object { ($_ -replace "AWS_DYNAMODB_MATCHES_TABLE=", "").Trim() }) | Select-Object -First 1
    
    Write-Host "  S3: $S3_BUCKET"
    Write-Host "  Collection: $COLLECTION"
}
else {
    $S3_BUCKET = "face-recognition-bucket"
    $COLLECTION = "face-recognition-collection-dev"
    $PEOPLE_TABLE = "face-recognition-people-dev"
    $MATCHES_TABLE = "face-recognition-matches-dev"
}

$ROLE_NAME = "lambda-face-recognition-role"
$FUNCTION_NAME = "face-identify-handler"

# Step 1: Create IAM Role
Write-Host "`n📝 Step 1: IAM Role..." -ForegroundColor Yellow
$roleCheck = aws iam get-role --role-name $ROLE_NAME 2>$null
if (!$?) {
    Write-Host "  Creating role..."
    
    $trust = @"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
"@
    
    Set-Content "trust.json" $trust
    aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://trust.json | Out-Null
    Remove-Item "trust.json"
    
    # Attach policies
    "service-role/AWSLambdaBasicExecutionRole", "AmazonRekognitionFullAccess", "AmazonS3FullAccess", "AmazonDynamoDBFullAccess" | ForEach-Object {
        aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn "arn:aws:iam::aws:policy/$_" | Out-Null
    }
    
    Write-Host "  ⏳ Waiting 15s for propagation..."
    Start-Sleep -Seconds 15
    Write-Host "  ✅ Role created" -ForegroundColor Green
}
else {
    Write-Host "  ✅ Role exists" -ForegroundColor Green
}

$ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

# Step 2: Package Lambda
Write-Host "`n📦 Step 2: Packaging..." -ForegroundColor Yellow
Push-Location ".\aws\backend\lambda\functions\identify-handler"
if (Test-Path "lambda-package.zip") { Remove-Item "lambda-package.zip" }
Compress-Archive -Path "lambda_function.py" -DestinationPath "lambda-package.zip" -Force
Write-Host "  ✅ Package created" -ForegroundColor Green

# Step 3: Deploy Lambda
Write-Host "`n🚀 Step 3: Deploying Lambda..." -ForegroundColor Yellow

$funcCheck = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>$null
if (!$?) {
    Write-Host "  Creating function..."
    aws lambda create-function `
        --function-name $FUNCTION_NAME `
        --runtime python3.11 `
        --role $ROLE_ARN `
        --handler lambda_function.lambda_handler `
        --zip-file fileb://lambda-package.zip `
        --timeout 30 `
        --memory-size 512 `
        --environment "Variables={AWS_REGION=$REGION,AWS_REKOGNITION_COLLECTION=$COLLECTION,AWS_S3_BUCKET=$S3_BUCKET,PERSON_TABLE=$PEOPLE_TABLE,MATCHES_TABLE=$MATCHES_TABLE,LOG_LEVEL=INFO}" `
        --region $REGION | Out-Null
    
    if ($?) {
        Write-Host "  ✅ Function created" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Failed to create function" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}
else {
    Write-Host "  Updating function..."
    aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://lambda-package.zip --region $REGION | Out-Null
    aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment "Variables={AWS_REGION=$REGION,AWS_REKOGNITION_COLLECTION=$COLLECTION,AWS_S3_BUCKET=$S3_BUCKET,PERSON_TABLE=$PEOPLE_TABLE,MATCHES_TABLE=$MATCHES_TABLE,LOG_LEVEL=INFO}" --region $REGION | Out-Null
    Write-Host "  ✅ Function updated" -ForegroundColor Green
}

Remove-Item "lambda-package.zip"
Pop-Location

# Step 4: API Gateway
Write-Host "`n🌐 Step 4: API Gateway..." -ForegroundColor Yellow
$apis = aws apigatewayv2 get-apis --region $REGION | ConvertFrom-Json
$api = $apis.Items | Where-Object { $_.Name -eq "face-recognition-api" }

if (!$api) {
    Write-Host "  Creating API..."
    $apiRes = aws apigatewayv2 create-api --name face-recognition-api --protocol-type HTTP --cors-configuration "AllowOrigins=*,AllowMethods=*,AllowHeaders=*" --region $REGION | ConvertFrom-Json
    $API_ID = $apiRes.ApiId
}
else {
    $API_ID = $api.ApiId
    Write-Host "  ✅ API exists: $API_ID" -ForegroundColor Green
}

# Create integration
$LAMBDA_ARN = "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}"
$integration = aws apigatewayv2 create-integration --api-id $API_ID --integration-type AWS_PROXY --integration-uri $LAMBDA_ARN --payload-format-version "2.0" --region $REGION 2>$null | ConvertFrom-Json

if ($integration) {
    $INTEGRATION_ID = $integration.IntegrationId
    aws apigatewayv2 create-route --api-id $API_ID --route-key "POST /identify" --target "integrations/$INTEGRATION_ID" --region $REGION 2>$null | Out-Null
}

aws apigatewayv2 create-stage --api-id $API_ID --stage-name prod --auto-deploy --region $REGION 2>$null | Out-Null

# Permission
aws lambda add-permission --function-name $FUNCTION_NAME --statement-id "api-$(Get-Random)" --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/*" --region $REGION 2>$null | Out-Null

$ENDPOINT = "https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"

Write-Host "`n" + "="*50 -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green
Write-Host "`n📌 API Endpoint:" -ForegroundColor Cyan
Write-Host "  $ENDPOINT" -ForegroundColor White
Write-Host "`n🧪 Test:" -ForegroundColor Yellow
Write-Host "  curl -X POST $ENDPOINT/identify -d '{""image_base64"":""...""}'" -ForegroundColor Gray
Write-Host ""

# Save endpoint
$ENDPOINT | Out-File "api-endpoint.txt" -Encoding utf8
