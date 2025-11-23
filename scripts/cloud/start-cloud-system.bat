@echo off
echo ============================================
echo   Face Recognition - CLOUD SYSTEM LAUNCH
echo ============================================
echo.
echo Starting Backend API with AWS Integration...
echo (Requires AWS Credentials in .env or Environment)
echo.

REM Get Project Root (2 levels up from scripts\local)
set "PROJECT_ROOT=%~dp0..\.."
cd /d "%PROJECT_ROOT%"

REM Activate Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo Warning: .venv not found! Using system python...
)

cd backend

REM Set Environment Variables for Cloud Mode
set AWS_REGION=us-east-1
REM Add other necessary env vars here if not in .env

start "Backend API - Cloud Mode" python src/api/app.py

timeout /t 5 /nobreak >nul

echo.
echo Starting Desktop Application...
echo.

start "Desktop App" /D "%PROJECT_ROOT%\frontend\desktop" npm run dev

echo.
echo ============================================
echo   SYSTEM STARTED (CLOUD MODE)!
echo ============================================
echo.
echo Backend API: http://127.0.0.1:8000 (Default for app.py)
echo API Docs: http://127.0.0.1:8000/docs
echo.
echo Desktop App: Check window "Desktop App"
echo.
echo Press any key to exit...
pause >nul
