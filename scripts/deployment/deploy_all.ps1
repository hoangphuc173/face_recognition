$ErrorActionPreference = "Stop"

Write-Host "Starting Full System Deployment..."

# 1. Build Lambda Layer
Write-Host "Step 1: Building Lambda Layer..."
.\scripts\build_layer.ps1

# 2. Deploy Infrastructure (Backend)
Write-Host "Step 2: Deploying Infrastructure..."
Set-Location infrastructure
npx cdk deploy --require-approval never
Set-Location ..

# 3. Build Frontend (Web)
Write-Host "Step 3: Building Web Frontend..."
Set-Location frontend\web
npm install
npm run build
Set-Location ..\..

# 4. Install Frontend (Desktop)
Write-Host "Step 4: Installing Desktop Frontend dependencies..."
Set-Location frontend\desktop
npm install
Set-Location ..\..

Write-Host "Deployment Complete!"
Write-Host "Note: Desktop app must be built and distributed manually using 'npm run tauri build' in frontend/desktop."
