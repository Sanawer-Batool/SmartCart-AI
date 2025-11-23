@echo off
echo ========================================
echo Starting SmartCart AI Backend (FIXED)
echo ========================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting server (no auto-reload to avoid Windows subprocess issues)...
echo Backend will be available at: http://localhost:8000
echo.
echo IMPORTANT: If you make code changes, restart this script manually.
echo.

python start-production.py

pause

