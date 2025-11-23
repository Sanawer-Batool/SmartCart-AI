#!/bin/bash
# Quick start script for SmartCart AI
# Starts both backend and frontend in separate terminal sessions

echo "╔═══════════════════════════════════════════════════════╗"
echo "║         SmartCart AI - Quick Start Script            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend virtual environment not found!"
    echo "   Please run: cd backend && python -m venv venv && source venv/bin/activate && python setup.py"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not found!"
    echo "   Please run: cd frontend && npm install"
    exit 1
fi

echo "🚀 Starting SmartCart AI..."
echo ""

# Start backend in background
echo "📦 Starting backend on http://localhost:8000"
cd backend
source venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "🎨 Starting frontend on http://localhost:3000"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║                   Services Started!                   ║"
echo "╠═══════════════════════════════════════════════════════╣"
echo "║  Backend:  http://localhost:8000                      ║"
echo "║  Frontend: http://localhost:3000                      ║"
echo "║  API Docs: http://localhost:8000/docs                 ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Register cleanup function
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait

