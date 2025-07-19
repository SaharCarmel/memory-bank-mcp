# PC Cortex - Memory Bank Builder

A comprehensive memory bank builder and management system that uses Claude Code SDK to analyze codebases and create detailed documentation.

## Project Structure

```
pc_cortex/
├── backend/          # FastAPI backend server
├── frontend/         # React frontend dashboard
├── mcp_server/       # MCP (Model Context Protocol) server
├── scripts/          # Utility scripts and CLI tools
├── demo_repo/        # Example repository for testing
└── system_prompt.md  # Core prompt for memory bank generation
```

## Quick Start

### Start the Dashboard

```bash
./scripts/start_dashboard.sh
```

This will:
1. Start the backend server on http://localhost:8000
2. Start the frontend on http://localhost:5174
3. Open the dashboard in your browser

### Start the Complete System

```bash
./scripts/start_system.sh
```

This starts all components including the MCP server.

## Features

- **Web Dashboard**: Interactive UI for building and managing memory banks
- **Real-time Progress**: Live streaming of build logs
- **Multiple Build Modes**: Full build or incremental updates
- **Task Management**: Track and organize development tasks
- **MCP Integration**: Expose memory banks via Model Context Protocol

## Memory Bank Structure

Each memory bank contains:
- `projectbrief.md` - Project overview and goals
- `productContext.md` - User needs and problems solved
- `systemPatterns.md` - Architecture and design patterns
- `techContext.md` - Technologies and setup
- `activeContext.md` - Current focus and recent changes
- `progress.md` - Implementation status
- `tasks/` - Task tracking and management

## Development

### Backend Setup
```bash
cd backend
uv venv
uv pip install -e .
uv run python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## API Documentation

When the backend is running, visit:
- Interactive API docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## CLI Tools

Additional CLI tools are available in `scripts/cli_tools/` for manual operations and scripting.