# PC Cortex - Memory Bank Builder & Observability Dashboard

A sophisticated memory bank builder that analyzes codebases and generates structured documentation for persistent project understanding, now with a comprehensive observability dashboard.

## Components

### 1. Memory Bank Builder
Uses Claude Code to analyze your codebase and generate a comprehensive "memory bank" - a structured set of markdown files that capture:

- Project overview and requirements
- Product context and user goals  
- System architecture and patterns
- Technical stack and dependencies
- Current development status
- Progress tracking

### 2. Observability Dashboard
A modern web-based dashboard for monitoring and managing memory banks with:

- **Frontend**: React 18 + Tailwind CSS + Vite (Port 3333)
- **Backend**: FastAPI + Python 3.11 (Port 8888)
- **Data Storage**: File system (with database migration readiness)
- **Real-time**: WebSocket connections for live updates

## Quick Start - Dashboard

### Prerequisites

- **Python 3.11+** with `uv` package manager
- **Node.js 18+** with `npm`

### Backend Setup

```bash
cd backend
./start.sh
```

The backend will be available at:
- API: http://localhost:8888
- Documentation: http://localhost:8888/docs
- WebSocket: ws://localhost:8888/api/v1/ws/updates

### Frontend Setup

```bash
cd frontend
npm install
./start.sh
```

The frontend will be available at:
- Dashboard: http://localhost:3333

## Dashboard Features

### 🎯 Dashboard Overview
- Real-time system metrics
- Generation statistics
- Recent activity feed
- System health monitoring

### 📁 File Management
- Interactive file tree navigation
- File content preview
- Search and filtering
- Upload and download capabilities

### 📊 Task Management
- Task creation and tracking
- Status management (pending, in-progress, completed)
- Priority-based organization
- Real-time status updates

### 🔗 Graph Visualization
- Interactive network diagrams
- Node and edge filtering
- Layout customization
- Relationship exploration

### ⚡ Real-time Updates
- WebSocket-based live updates
- Connection status monitoring
- Automatic reconnection
- Toast notifications

## Memory Bank Builder

## Installation

1. Install dependencies:
```bash
uv add claude-code-sdk
```

2. Ensure Claude CLI is installed:
```bash
npm install -g @anthropic-ai/claude-code
```

## Usage

### Quick Start

Use the convenience script:
```bash
# Analyze current directory (creates ./pc_cortex_memory_bank)
./build_memory_bank.sh

# Analyze specific repository (creates ./repo_name_memory_bank)
./build_memory_bank.sh /path/to/repo

# Custom output name
./build_memory_bank.sh /path/to/repo my_memory_bank
```

### Standalone Usage

Use the standalone script for any folder:
```bash
# Analyze current directory (creates ./current_memory_bank)
./pc_cortex

# Analyze specific repository (creates ./repo_name_memory_bank)
./pc_cortex /path/to/repo

# Custom output location
./pc_cortex /path/to/repo -o ./custom_output
```

### Direct Implementation Usage

```bash
uv run python3 memory_bank_builder_writer.py /path/to/repo -o ./output_dir -v
```

## Updating Memory Bank

Once you have a memory bank, you can update it based on code changes:

### Update based on git changes

```bash
# Update from last commit
./update_memory_bank.sh /path/to/repo ./repo_memory_bank

# Update from specific commit
./update_memory_bank.sh /path/to/repo ./repo_memory_bank --since-commit abc123

# Update from diff file
./update_memory_bank.sh /path/to/repo ./repo_memory_bank changes.diff

# Update from stdin
git diff | ./update_memory_bank.sh /path/to/repo ./repo_memory_bank --stdin
```

### Direct usage

```bash
# From commit
uv run python3 update_memory_bank.py /path/to/repo ./repo_memory_bank --since-commit HEAD~1

# From diff file
uv run python3 update_memory_bank.py /path/to/repo ./repo_memory_bank --diff-file changes.diff

# From stdin
git diff | uv run python3 update_memory_bank.py /path/to/repo ./repo_memory_bank --diff-stdin
```

## Output Structure

The memory bank creates the following structure:

```
output_dir/
├── memory-bank/
│   ├── projectbrief.md      # Project overview and requirements
│   ├── productContext.md    # Why this exists, user goals
│   ├── systemPatterns.md    # Architecture and design patterns
│   ├── techContext.md       # Tech stack and dependencies
│   ├── activeContext.md     # Current development focus
│   ├── progress.md          # What's done and what's pending
│   └── tasks/
│       └── _index.md        # Task tracking index
├── graph.json               # Graph structure for relationships
└── generation_summary.json  # Generation metadata
```

## Core Components

- **pc_cortex** - Standalone script for analyzing any codebase
- **memory_bank_builder_writer.py** - Core implementation using Claude Code SDK
- **build_memory_bank.sh** - Convenience script with fallback strategies
- **update_memory_bank.py** - Update memory bank based on git changes
- **update_memory_bank.sh** - Convenience script for updating memory bank
- **system_prompt.md** - System prompt for Claude analysis

## Requirements

- Python 3.11+
- Claude API key (set as ANTHROPIC_API_KEY)
- Node.js (for Claude CLI)

## License

Apache 2.0