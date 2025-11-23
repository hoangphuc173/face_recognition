@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo      Promote User to Admin (Face Recognition)
echo ========================================================

REM Check if username is provided
if "%~1"=="" (
    echo Usage: promote-admin.bat ^<username^>
    echo Example: promote-admin.bat admin
    exit /b 1
)

set USERNAME=%~1

REM Try to find User Pool ID from backend-outputs.json
if exist "..\infrastructure\backend-outputs.json" (
    for /f "tokens=*" %%a in ('type ..\infrastructure\backend-outputs.json ^| findstr "UserPoolId"') do (
        set LINE=%%a
        REM Extract value (rough parsing)
        for /f "tokens=2 delims=:," %%b in ("!LINE!") do (
            set POOL_ID=%%b
            REM Trim quotes and spaces
            set POOL_ID=!POOL_ID:"=!
            set POOL_ID=!POOL_ID: =!
        )
    )
)

REM If not found in file, ask user or try to find via AWS CLI
if "!POOL_ID!"=="" (
    echo Could not find UserPoolId in output file.
    echo Trying to find via AWS CLI...
    for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name FaceRecogBackendStack --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text') do set POOL_ID=%%i
)

if "!POOL_ID!"=="" (
    echo Error: Could not find User Pool ID. Please ensure backend is deployed.
    exit /b 1
)

echo.
echo User Pool ID: !POOL_ID!
echo Promoting user '!USERNAME!' to Admin group...
echo.

aws cognito-idp admin-add-user-to-group --user-pool-id !POOL_ID! --username !USERNAME! --group-name Admin

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Success! User '!USERNAME!' is now an Admin.
    echo They can now access Admin features in the app.
) else (
    echo.
    echo ❌ Failed to promote user.
    echo Please check if the username exists and you have permissions.
)

echo.
pause
