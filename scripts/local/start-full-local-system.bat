@echo off
echo ============================================
echo   Face Recognition - LOCAL SYSTEM
echo ============================================
echo.
echo Starting Backend API (Local Mode with Auth + OTP)...
echo.

REM Get Project Root
set "PROJECT_ROOT=%~dp0..\.."
cd /d "%PROJECT_ROOT%"

REM Activate Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

cd backend
start "Backend API - Local" python src/api/local_full_app.py

timeout /t 3 /nobreak >nul

echo.
echo Starting Desktop Application...
echo.

start "Desktop App" /D "%PROJECT_ROOT%\frontend\desktop" npm run dev

echo.
echo ============================================
echo   SYSTEM STARTED!
echo ============================================
echo.
echo Backend API: http://127.0.0.1:5555
echo API Docs: http://127.0.0.1:5555/docs
echo.
echo Desktop App: Check window "Desktop App"
echo.
echo Features:
echo   - User Registration with OTP
echo   - Face Enrollment (per-user folders)
echo   - Login / Authentication
echo   - Local storage (no AWS needed)
echo.
echo Press any key to exit...
pause >nul
