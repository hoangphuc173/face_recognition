$ErrorActionPreference = "Stop"

Write-Host "Running Tests..."

# Backend Tests
Write-Host "Testing Backend..."
# pytest would go here if we had tests set up
# pytest backend/tests

# Infrastructure Tests
Write-Host "Testing Infrastructure..."
Set-Location infrastructure
npm test
Set-Location ..

Write-Host "Tests Complete!"
