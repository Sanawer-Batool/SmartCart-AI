@echo off
echo ===========================================
echo   SmartCart AI Backend Restart Script
echo ===========================================
echo.

echo [1/3] Killing old processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Clearing Python cache...
cd /d "%~dp0"
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul

echo [3/3] Starting fresh backend...
call venv\Scripts\activate.bat
python run_server.py

pause
