param (
    [string]$ApiKey
)

# 1. Find the Auth Function
Write-Host "Finding Auth Lambda function..."
$functionName = aws lambda list-functions --query "Functions[?contains(FunctionName, 'AuthHandler')].FunctionName" --output text

if (-not $functionName) {
    Write-Error "Could not find AuthHandler function. Make sure you have deployed the backend."
    exit 1
}

Write-Host "Found function: $functionName" -ForegroundColor Green

# 2. Get Credentials
if (-not $ApiKey) {
    $ApiKey = Read-Host "Enter your Brevo API Key"
}

if (-not $ApiKey) {
    Write-Error "API Key is required."
    exit 1
}

# 3. Update Configuration
Write-Host "Updating Lambda configuration..."
$envVars = aws lambda get-function-configuration --function-name $functionName --query "Environment.Variables" --output json | ConvertFrom-Json

# Add new variables
$envVars | Add-Member -MemberType NoteProperty -Name "BREVO_API_KEY" -Value $apiKey -Force

# Construct JSON
$variables = @{}
$envVars.PSObject.Properties | ForEach-Object {
    $variables[$_.Name] = $_.Value
}
$variables["BREVO_API_KEY"] = $apiKey

$jsonPayload = $variables | ConvertTo-Json -Compress
$tempFile = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tempFile -Value "{ ""Variables"": $jsonPayload }"

try {
    aws lambda update-function-configuration --function-name $functionName --environment file://$tempFile
    Write-Host ""
    Write-Host "✅ Configuration updated successfully!" -ForegroundColor Green
    Write-Host "You can now use the registration with Brevo OTP."
}
catch {
    Write-Error "Failed to update configuration."
    Write-Host $_
}
finally {
    Remove-Item $tempFile
}
