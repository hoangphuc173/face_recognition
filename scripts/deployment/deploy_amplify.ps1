# Deploy to AWS Amplify (Manual Deployment via Console)
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying to AWS Amplify" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Next.js app
Write-Host "Step 1/2: Building Next.js app..." -ForegroundColor Yellow
Push-Location frontend/web
npm install
npm run export
Pop-Location
Write-Host "✅ Build complete" -ForegroundColor Green
Write-Host ""

# Step 2: Get Amplify App ID
Write-Host "Step 2/2: Getting Amplify App ID..." -ForegroundColor Yellow
$appId = aws cloudformation describe-stacks --stack-name FaceRecogAmplifyStack --query "Stacks[0].Outputs[?OutputKey=='AmplifyAppId'].OutputValue" --output text

if (-not $appId) {
    Write-Host "❌ Amplify App ID not found! Did you deploy the stack?" -ForegroundColor Red
    exit 1
}
Write-Host "App ID: $appId" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "MANUAL DEPLOYMENT REQUIRED" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "AWS Amplify CLI-based deployment có vấn đề với manual apps." -ForegroundColor Gray
Write-Host "Vui lòng làm theo các bước sau để deploy thủ công:" -ForegroundColor White
Write-Host ""
Write-Host "1. Mở Amplify Console:" -ForegroundColor Cyan
Write-Host "   https://console.aws.amazon.com/amplify/home?region=us-east-1#/$appId" -ForegroundColor White
Write-Host ""
Write-Host "2. Click vào branch 'prod'" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Click 'Deploy updates' > 'Drag and drop'" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Kéo thả toàn bộ nội dung trong thư mục:" -ForegroundColor Cyan
Write-Host "   frontend/web/out/" -ForegroundColor White
Write-Host ""
Write-Host "Hoặc nếu muốn tự động hơn, hãy kết nối GitHub repository." -ForegroundColor Gray
Write-Host ""
