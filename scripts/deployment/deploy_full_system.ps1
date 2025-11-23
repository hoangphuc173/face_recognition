# Automated Deployment Script for Face Recognition System
# This script deploys the Cognito-integrated backend to AWS

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Face Recognition System - Full Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Lambda Layer
Write-Host "Step 1/5: Building Lambda Layer..." -ForegroundColor Yellow
Push-Location scripts
.\build_layer.ps1
Pop-Location
Write-Host "✅ Lambda layer built successfully" -ForegroundColor Green
Write-Host ""

# Step 2: Deploy CDK Stack
Write-Host "Step 2/5: Deploying CDK Infrastructure..." -ForegroundColor Yellow
Push-Location infrastructure

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing CDK dependencies..." -ForegroundColor Gray
    npm install
}

# Deploy with auto-approval
Write-Host "Deploying to AWS (this may take 5-10 minutes)..." -ForegroundColor Gray
npx cdk deploy --require-approval never --outputs-file outputs.json

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ CDK deployment failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "✅ CDK stack deployed successfully" -ForegroundColor Green
Pop-Location
Write-Host ""

# Step 3: Extract Outputs
Write-Host "Step 3/5: Extracting deployment outputs..." -ForegroundColor Yellow

$outputsPath = "infrastructure/outputs.json"
if (-not (Test-Path $outputsPath)) {
    Write-Host "❌ Outputs file not found!" -ForegroundColor Red
    exit 1
}

$outputs = Get-Content $outputsPath | ConvertFrom-Json
$stackName = ($outputs | Get-Member -MemberType NoteProperty).Name
$stackOutputs = $outputs.$stackName

$apiUrl = $stackOutputs.ApiUrl
$userPoolId = $stackOutputs.UserPoolId
$userPoolClientId = $stackOutputs.UserPoolClientId

Write-Host "API URL: $apiUrl" -ForegroundColor Cyan
Write-Host "User Pool ID: $userPoolId" -ForegroundColor Cyan
Write-Host "Client ID: $userPoolClientId" -ForegroundColor Cyan
Write-Host "✅ Outputs extracted" -ForegroundColor Green
Write-Host ""

# Step 4: Create Admin User in Cognito
Write-Host "Step 4/5: Creating Admin User..." -ForegroundColor Yellow

$adminUsername = Read-Host "Enter admin username (default: admin)"
if ([string]::IsNullOrWhiteSpace($adminUsername)) {
    $adminUsername = "admin"
}

$adminEmail = Read-Host "Enter admin email"
if ([string]::IsNullOrWhiteSpace($adminEmail)) {
    Write-Host "❌ Admin email is required!" -ForegroundColor Red
    exit 1
}

$adminPassword = Read-Host "Enter admin password (min 8 chars, must include uppercase, lowercase, number, special char)" -AsSecureString
$adminPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPassword))

Write-Host "Creating Cognito user..." -ForegroundColor Gray

# Create user
aws cognito-idp admin-create-user `
    --user-pool-id $userPoolId `
    --username $adminUsername `
    --user-attributes Name=email, Value=$adminEmail Name=email_verified, Value=true `
    --message-action SUPPRESS

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  User might already exist, continuing..." -ForegroundColor Yellow
}

# Set permanent password
aws cognito-idp admin-set-user-password `
    --user-pool-id $userPoolId `
    --username $adminUsername `
    --password $adminPasswordPlain `
    --permanent

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set password!" -ForegroundColor Red
    exit 1
}

# Add to Admin group
aws cognito-idp admin-add-user-to-group `
    --user-pool-id $userPoolId `
    --username $adminUsername `
    --group-name Admin

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to add user to Admin group!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Admin user created successfully" -ForegroundColor Green
Write-Host ""

# Step 5: Update Frontend Configuration
Write-Host "Step 5/5: Updating Frontend Configuration..." -ForegroundColor Yellow

# Update desktop app .env
$desktopEnvPath = "frontend/desktop/.env.production"
$envContent = @"
VITE_API_BASE_URL=$apiUrl
"@

Set-Content -Path $desktopEnvPath -Value $envContent
Write-Host "✅ Desktop app .env.production created" -ForegroundColor Green

# Update web app .env
$webEnvPath = "frontend/web/.env.production"
Set-Content -Path $webEnvPath -Value $envContent
Write-Host "✅ Web app .env.production created" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE! 🎉" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Deployment Summary:" -ForegroundColor Yellow
Write-Host "  API URL: $apiUrl" -ForegroundColor White
Write-Host "  User Pool ID: $userPoolId" -ForegroundColor White
Write-Host "  Client ID: $userPoolClientId" -ForegroundColor White
Write-Host ""
Write-Host "Admin Credentials:" -ForegroundColor Yellow
Write-Host "  Username: $adminUsername" -ForegroundColor White
Write-Host "  Email: $adminEmail" -ForegroundColor White
Write-Host "  Password: [as entered]" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test backend: curl $apiUrl" -ForegroundColor White
Write-Host "  2. Build desktop app: cd frontend/desktop && npm run tauri build" -ForegroundColor White
Write-Host "  3. Deploy web app: cd frontend/web && npm run build" -ForegroundColor White
Write-Host ""
Write-Host "Save this information securely!" -ForegroundColor Red
Write-Host ""
