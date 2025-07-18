#!/bin/bash

# Memory Bank Dashboard Startup Script
# This script starts both backend and frontend servers

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Memory Bank Dashboard ===${NC}"

# Function to cleanup background processes
cleanup() {
    echo -e "\n${RED}Shutting down services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Services stopped.${NC}"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Start backend
echo -e "${GREEN}Starting backend server...${NC}"
cd backend
uv run python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}Starting frontend server...${NC}"
cd ../frontend
npm start &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

echo -e "${GREEN}=== Services Started ===${NC}"
echo -e "Backend: ${BLUE}http://localhost:8888${NC}"
echo -e "Frontend: ${BLUE}http://localhost:3333${NC}"
echo -e "API Docs: ${BLUE}http://localhost:8888/docs${NC}"
echo -e "\nPress Ctrl+C to stop all services"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID