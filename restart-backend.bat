@echo off
echo Restarting Backend API Server...
echo.

REM Kill existing process on port 5555
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5555') do (
    echo Killing process %%a
    taskkill /F /PID %%a 2>nul
)

timeout /t 2 /nobreak >nul

echo Starting backend...
cd aws
start "Backend API" python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 5555 --reload

echo.
echo Backend API restarted!
echo Check window "Backend API" for logs
echo.
pause

