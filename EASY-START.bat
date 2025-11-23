@echo off
REM Easy startup script for SmartCart AI
REM Double-click this file to start everything!

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║         SmartCart AI - Easy Start                     ║
echo ║                                                       ║
echo ║  This will start both backend and frontend           ║
echo ║  Two windows will open - keep them running!          ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo 🚀 Starting SmartCart AI...
echo.

REM Check if setup is done
if not exist "backend\venv" (
    echo ⚠️  First time setup needed!
    echo.
    echo Running setup... This will take a few minutes.
    echo.
    
    REM Setup backend
    echo 📦 Setting up backend...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    python -m playwright install chromium
    cd ..
    
    REM Setup frontend
    echo 📦 Setting up frontend...
    cd frontend
    call npm install
    cd ..
    
    echo.
    echo ✅ Setup complete!
    echo.
)

REM Start backend
echo 🔧 Starting backend on http://localhost:8000
start "SmartCart AI - Backend" cmd /k "cd backend && venv\Scripts\activate && python app.py"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend
echo 🎨 Starting frontend on http://localhost:3000
start "SmartCart AI - Frontend" cmd /k "cd frontend && npm run dev"

REM Wait a bit more
timeout /t 3 /nobreak >nul

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║              ✅ SmartCart AI is Starting!             ║
echo ╠═══════════════════════════════════════════════════════╣
echo ║                                                       ║
echo ║  🌐 Open your browser and go to:                     ║
echo ║                                                       ║
echo ║     http://localhost:3000                            ║
echo ║                                                       ║
echo ║  ───────────────────────────────────────────────────  ║
echo ║                                                       ║
echo ║  📝 To use it:                                        ║
echo ║                                                       ║
echo ║  1. Website URL: https://amazon.com                  ║
echo ║  2. Goal: Find cheap laptops under $500              ║
echo ║  3. Click "Start Mission"                            ║
echo ║  4. Watch it work! ✨                                ║
echo ║                                                       ║
echo ║  ───────────────────────────────────────────────────  ║
echo ║                                                       ║
echo ║  ⚠️  Keep the two terminal windows open!             ║
echo ║     (They're running the backend and frontend)       ║
echo ║                                                       ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM Try to open browser automatically
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo 🎉 Browser should open automatically!
echo    If not, manually go to: http://localhost:3000
echo.
pause

