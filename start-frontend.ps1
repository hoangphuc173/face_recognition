# Start Frontend UI Application
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Starting Face Recognition UI App" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path "$PSScriptRoot\face-recognition-app"

Write-Host "Starting Vite dev server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Once started, open your browser to:" -ForegroundColor Green
Write-Host "  http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Login with:" -ForegroundColor Green
Write-Host "  Username: admin" -ForegroundColor Green
Write-Host "  Password: admin123" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

npm run dev

