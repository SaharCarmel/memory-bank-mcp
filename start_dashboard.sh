#!/bin/bash

echo "Starting Memory Bank Dashboard..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start the backend
echo "Starting FastAPI backend..."
cd "$SCRIPT_DIR/backend" && uv run uvicorn main:app --reload --port 8888 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start the frontend
echo "Starting React frontend..."
cd "$SCRIPT_DIR/frontend" && PORT=3333 npm start &
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
echo "Backend: http://localhost:8888"
echo "Frontend: http://localhost:3333"
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait