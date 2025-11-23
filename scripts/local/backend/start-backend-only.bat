@echo off
echo ============================================
echo   Backend API - Local Mode
echo ============================================
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

echo.
echo Starting Backend API on port 5555...
echo.

cd backend
python src/api/local_full_app.py

pause
