#!/bin/bash

echo "Starting PC Cortex Dashboard..."

# Get the project root directory (parent of scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Start the backend
echo "Starting FastAPI backend..."
cd "$PROJECT_ROOT/backend" && uv run uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start the frontend
echo "Starting React frontend..."
cd "$PROJECT_ROOT/frontend" && npm run dev &
FRONTEND_PID=$!

# Function to cleanup on script exit
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap cleanup function on script exit
trap cleanup EXIT

echo "Dashboard started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5174"
echo "Opening dashboard in browser..."
sleep 2
open http://localhost:5174 2>/dev/null || xdg-open http://localhost:5174 2>/dev/null || echo "Please open http://localhost:5174 in your browser"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait