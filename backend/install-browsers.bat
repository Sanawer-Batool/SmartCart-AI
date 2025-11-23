@echo off
REM Install Playwright browsers for SmartCart AI

echo ====================================
echo Installing Playwright Browsers
echo ====================================
echo.

REM Activate virtual environment
call venv\Scripts\activate

echo Installing Chromium browser for Playwright...
python -m playwright install chromium

echo.
echo ====================================
echo Installation Complete!
echo ====================================
echo.
echo You can now start the backend server with: python app.py
echo.

pause

