@echo off
echo ============================================
echo   Backend API - FULL CLOUD MODE
echo ============================================
echo.
echo Requires AWS Credentials configured!
echo.

REM Get Project Root
set "PROJECT_ROOT=%~dp0..\.."
cd /d "%PROJECT_ROOT%"

REM Activate Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    echo Activating .venv...
    call ".venv\Scripts\activate.bat"
) else (
    echo Warning: .venv not found!
)

REM Set PYTHONPATH to include project root
set PYTHONPATH=%CD%;%PYTHONPATH%

echo.
echo PYTHONPATH: %PYTHONPATH%
echo.
echo Starting Backend API (Cloud Mode - Simplified)...
echo.

cd backend\src\api

REM Run simplified cloud app
python app_cloud_simple.py

pause
