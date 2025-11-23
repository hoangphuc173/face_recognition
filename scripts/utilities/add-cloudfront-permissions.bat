@echo off
REM Add CloudFront Full Access to current AWS user

echo Getting current AWS user...
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query "Arn" --output text') do set ARN=%%i

REM Extract username from ARN
for /f "tokens=2 delims=/" %%j in ("%ARN%") do set USERNAME=%%j

echo Current user: %USERNAME%
echo.
echo Adding CloudFrontFullAccess policy...

aws iam attach-user-policy --user-name %USERNAME% --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Successfully attached CloudFrontFullAccess policy!
    echo.
    echo Waiting 10 seconds for IAM to propagate...
    timeout /t 10 /nobreak >nul
    echo.
    echo ✅ Ready to deploy!
) else (
    echo.
    echo ❌ Failed to attach policy. You may need admin permissions.
    echo Please use AWS Console to add CloudFrontFullAccess policy manually.
)

pause
