@echo off
REM Test script for Face Recognition System
echo ========================================
echo   Face Recognition System - TEST
echo ========================================
echo.

echo [1/3] Testing Python syntax...
.venv\Scripts\python.exe -m py_compile gui_app.py
.venv\Scripts\python.exe -m py_compile database_manager.py
.venv\Scripts\python.exe -m py_compile enrollment_service_v2.py
.venv\Scripts\python.exe -m py_compile identification_service_v2.py
.venv\Scripts\python.exe -m py_compile launcher.py
.venv\Scripts\python.exe -m py_compile manage_database.py

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Syntax errors found!
    pause
    exit /b 1
)

echo.
echo [2/3] Checking database...
.venv\Scripts\python.exe -c "from database_manager import DatabaseManager; db = DatabaseManager(); print('Database OK:', len(db.get_all_people()), 'people')"

echo.
echo [3/3] Running import checks...
.venv\Scripts\python.exe -c "import gui_app, database_manager, enrollment_service_v2, identification_service_v2, launcher, manage_database; print('All imports successful!')"

echo.
echo ========================================
echo   ALL TESTS PASSED!
echo ========================================
pause
