@echo off
echo ============================================
echo   Face Recognition - FULL SYSTEM LAUNCH
echo ============================================
echo.
echo Starting Backend API with FULL FEATURES...
echo (Using local storage - no AWS needed)
echo.

cd aws\backend\api
start "Backend API - Full Features" python local_full_app.py

timeout /t 5 /nobreak >nul

echo.
echo Starting Desktop Application...
echo.

cd ..\..\..
start "Desktop App" python app\gui_app.py

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
echo   - Face Enrollment with REAL Person ID
echo   - Face Identification (simulated)
echo   - People Management (full CRUD)
echo   - Local storage (local_data/ folder)
echo.
echo Press any key to exit...
pause >nul

