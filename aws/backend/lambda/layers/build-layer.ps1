# Build Lambda Layer with Python dependencies (Windows)

Write-Host '📦 Building Lambda Layer...' -ForegroundColor Cyan

# Work in current directory
$layerDir = "python-deps"
$outputZip = "python-deps-layer.zip"

# Remove old build
if (Test-Path $layerDir) { Remove-Item -Recurse -Force $layerDir }
if (Test-Path $outputZip) { Remove-Item -Force $outputZip }

# Create structure
New-Item -ItemType Directory -Path "$layerDir\python" -Force | Out-Null

# Create requirements if not exists
if (-not (Test-Path "requirements.txt")) {
    @"
boto3==1.40.0
pillow==12.0.0
numpy==2.2.0
redis==5.2.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -t "$layerDir\python\" --no-cache-dir

# Create deployment package
Write-Host "Creating ZIP..." -ForegroundColor Yellow
Compress-Archive -Path "$layerDir\*" -DestinationPath $outputZip -Force

# Cleanup
Remove-Item -Recurse -Force $layerDir

Write-Host "✅ Lambda layer built: $outputZip" -ForegroundColor Green
Write-Host "Size: $((Get-Item $outputZip).Length / 1MB) MB" -ForegroundColor Cyan
