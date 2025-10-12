@echo off
REM Clean script for Face Recognition System
echo ========================================
echo   Face Recognition System - CLEAN
echo ========================================
echo.

echo [1/5] Cleaning __pycache__ folders...
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [2/5] Cleaning .pyc, .pyo files...
del /s /q *.pyc >nul 2>&1
del /s /q *.pyo >nul 2>&1

echo [3/5] Cleaning old .pkl files...
del /s /q *.pkl >nul 2>&1

echo [4/5] Cleaning temp folder...
if exist temp rd /s /q temp

echo [5/5] Cleaning recognized folder...
if exist recognized\*.* del /q recognized\*.*

echo.
echo ========================================
echo   CLEAN COMPLETED!
echo ========================================
pause
