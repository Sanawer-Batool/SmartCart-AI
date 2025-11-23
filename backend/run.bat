@echo off
REM Run script for SmartCart AI backend (Windows)

echo 🚀 Starting SmartCart AI Backend...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found!
    echo    Please create it first: python -m venv venv
    echo    Then activate it and run: python setup.py
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  Warning: .env file not found
    echo    The API might not work without GOOGLE_API_KEY
    echo.
)

REM Run the FastAPI app
echo Starting FastAPI server...
echo API will be available at: http://localhost:8000
echo Swagger docs at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

uvicorn app:app --reload --host 0.0.0.0 --port 8000

