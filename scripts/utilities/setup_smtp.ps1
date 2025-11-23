# Setup Gmail SMTP for Auth Lambda
Write-Host "=== Gmail SMTP Setup for Face Recognition App ===" -ForegroundColor Cyan
Write-Host "This script will configure your Lambda function to use Gmail for sending OTPs."
Write-Host "You need a Gmail address and an App Password."
Write-Host "To get an App Password: Go to Google Account -> Security -> 2-Step Verification -> App passwords."
Write-Host ""

# 1. Find the Auth Function
Write-Host "Finding Auth Lambda function..."
$functionName = aws lambda list-functions --query "Functions[?contains(FunctionName, 'AuthHandler')].FunctionName" --output text

if (-not $functionName) {
    Write-Error "Could not find AuthHandler function. Make sure you have deployed the backend."
    exit 1
}

Write-Host "Found function: $functionName" -ForegroundColor Green

# 2. Get Credentials
$email = Read-Host "Enter your Gmail address"
$password = Read-Host "Enter your Gmail App Password"

if (-not $email -or -not $password) {
    Write-Error "Email and Password are required."
    exit 1
}

# 3. Update Configuration
Write-Host "Updating Lambda configuration..."
$envVars = aws lambda get-function-configuration --function-name $functionName --query "Environment.Variables" --output json | ConvertFrom-Json

# Add new variables
$envVars | Add-Member -MemberType NoteProperty -Name "SMTP_USERNAME" -Value $email -Force
$envVars | Add-Member -MemberType NoteProperty -Name "SMTP_PASSWORD" -Value $password -Force

# Convert back to format expected by update-function-configuration
# We need to construct the string "Key=Value,Key=Value..." or use json
# The easiest way with AWS CLI is often just passing the variables we want to update if we use --environment "Variables={...}"
# But we need to preserve existing variables.

# Let's construct the JSON for the Variables object
$variables = @{}
$envVars.PSObject.Properties | ForEach-Object {
    $variables[$_.Name] = $_.Value
}
$variables["SMTP_USERNAME"] = $email
$variables["SMTP_PASSWORD"] = $password

$jsonPayload = $variables | ConvertTo-Json -Compress
# Escape quotes for command line if necessary, but PowerShell handling of JSON in args can be tricky.
# Let's write to a temp file to be safe.
$tempFile = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tempFile -Value "{ ""Variables"": $jsonPayload }"

try {
    aws lambda update-function-configuration --function-name $functionName --environment file://$tempFile
    Write-Host ""
    Write-Host "✅ Configuration updated successfully!" -ForegroundColor Green
    Write-Host "You can now use the registration with Gmail OTP."
}
catch {
    Write-Error "Failed to update configuration."
    Write-Host $_
}
finally {
    Remove-Item $tempFile
}
