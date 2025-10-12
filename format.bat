@echo off
REM Format script for Face Recognition System
echo ========================================
echo   Face Recognition System - FORMAT
echo ========================================
echo.

echo [1/2] Running isort to organize imports...
.venv\Scripts\python.exe -m isort . --profile black --line-length 100

echo.
echo [2/2] Running Black to format code...
.venv\Scripts\python.exe -m black . --line-length 100 --exclude="\.venv|\.git|__pycache__"

echo.
echo ========================================
echo   FORMAT COMPLETED!
echo ========================================
pause
