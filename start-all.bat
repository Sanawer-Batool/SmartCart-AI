@echo off
REM Quick start script for SmartCart AI (Windows)
REM Starts both backend and frontend

echo ╔═══════════════════════════════════════════════════════╗
echo ║         SmartCart AI - Quick Start Script            ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM Check if backend venv exists
if not exist "backend\venv" (
    echo ❌ Backend virtual environment not found!
    echo    Please run: cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& python setup.py
    exit /b 1
)

REM Check if frontend node_modules exists
if not exist "frontend\node_modules" (
    echo ❌ Frontend dependencies not found!
    echo    Please run: cd frontend ^&^& npm install
    exit /b 1
)

echo 🚀 Starting SmartCart AI...
echo.

REM Start backend in new window
echo 📦 Starting backend on http://localhost:8000
start "SmartCart AI - Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn app:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo 🎨 Starting frontend on http://localhost:3000
start "SmartCart AI - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║                   Services Started!                   ║
echo ╠═══════════════════════════════════════════════════════╣
echo ║  Backend:  http://localhost:8000                      ║
echo ║  Frontend: http://localhost:3000                      ║
echo ║  API Docs: http://localhost:8000/docs                 ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo Check the new terminal windows for logs
echo Close those windows to stop the services
echo.
pause

