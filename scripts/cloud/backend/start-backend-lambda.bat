@echo off
echo ============================================
echo   Backend API - LAMBDA MODE (Local)
echo ============================================
echo.
echo Simulating AWS Lambda environment locally
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

REM Add Lambda Layer to PYTHONPATH (this is where backend.core, backend.aws, etc. are)
set "PYTHONPATH=%CD%\backend\layer\python;%PYTHONPATH%"

echo.
echo PYTHONPATH configured with Lambda Layer
echo Layer path: %CD%\backend\layer\python
echo.
echo Starting Backend API (Lambda simulation)...
echo.

cd backend

REM Run app.py with Lambda layer in path
python src\api\app.py

pause
