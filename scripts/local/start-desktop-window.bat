@echo off
echo ============================================
echo   Face Recognition - DESKTOP WINDOW APP
echo ============================================
echo.
echo Starting Backend API...
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
echo Starting Desktop Window Application...
echo.

cd "%PROJECT_ROOT%\frontend\desktop"

REM Install dependencies if needed
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
)

REM Run Tauri Desktop App (opens as native window)
npm run tauri dev

echo.
echo Desktop app closed.
pause
