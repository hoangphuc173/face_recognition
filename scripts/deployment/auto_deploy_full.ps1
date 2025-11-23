# Automated Deployment Script for Face Recognition System (Non-Interactive)
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Face Recognition System - Full Deployment (Auto)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Default Credentials
$adminUsername = "admin"
$adminEmail = "admin@example.com"
$adminPasswordPlain = "Admin123!@#" 

# Step 1: Build Lambda Layer
Write-Host "Step 1/5: Building Lambda Layer..." -ForegroundColor Yellow
Push-Location scripts/utilities
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
npx cdk deploy --all --require-approval never --outputs-file outputs.json

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
# Handle multiple stacks if present, assume the main one has ApiUrl
foreach ($prop in $stackName) {
    if ($outputs.$prop.ApiUrl) {
        $stackOutputs = $outputs.$prop
        break
    }
}

if (-not $stackOutputs) {
    # Fallback to first one if logic above fails or just one stack
    $firstStack = $stackName[0]
    $stackOutputs = $outputs.$firstStack
}


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

Write-Host "Creating Cognito user..." -ForegroundColor Gray

# Create user
aws cognito-idp admin-create-user `
    --user-pool-id $userPoolId `
    --username $adminUsername `
    --user-attributes "Name=email,Value=$adminEmail" "Name=email_verified,Value=true" `
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
$webEnvContent = @"
NEXT_PUBLIC_API_URL=$apiUrl
"@
Set-Content -Path $webEnvPath -Value $webEnvContent
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
Write-Host "  Password: $adminPasswordPlain" -ForegroundColor White
Write-Host ""
