# CLI Usage Guide

The MemBankBuilder CLI is the core tool for generating memory banks from any codebase. This guide covers all CLI functionality with practical examples.

## Installation

### Prerequisites
- Python 3.11+
- UV (recommended Python package manager)

### Install UV
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows  
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install MemBankBuilder
```bash
# Clone the repository
git clone https://github.com/membank-builder/memory-bank-builder.git
cd memory-bank-builder

# Install dependencies
cd memory_bank_core && uv sync
```

## Basic Commands

### Build a Memory Bank

Generate a complete memory bank from any repository:

```bash
# Basic build
uv run python -m memory_bank_core build /path/to/your/repo

# Build with custom output name
uv run python -m memory_bank_core build /path/to/your/repo --output-name my-project

# Build and wait for completion (default behavior)
uv run python -m memory_bank_core build /path/to/your/repo --wait

# Build and return immediately (run in background)
uv run python -m memory_bank_core build /path/to/your/repo --no-wait
```

### Update Existing Memory Bank

Update an existing memory bank with recent changes:

```bash
# Update existing memory bank
uv run python -m memory_bank_core update /path/to/your/repo my-project-memory-bank

# Update with custom wait behavior
uv run python -m memory_bank_core update /path/to/your/repo my-project --no-wait
```

### List Memory Banks

View all generated memory banks:

```bash
# List all memory banks in current directory
uv run python -m memory_bank_core list

# List memory banks in specific directory  
uv run python -m memory_bank_core --root-path /custom/path list
```

### Background Worker

Start a persistent worker for processing multiple jobs:

```bash
# Start worker with default settings
uv run python -m memory_bank_core worker

# Start worker with custom concurrency
uv run python -m memory_bank_core worker --max-jobs 5

# Worker will process jobs until stopped with Ctrl+C
```

## Global Options

These options work with all commands:

```bash
# Set custom root directory for memory banks
uv run python -m memory_bank_core --root-path /my/memory/banks build /repo

# Enable verbose logging
uv run python -m memory_bank_core --verbose build /repo

# Combine options
uv run python -m memory_bank_core --root-path /output --verbose build /repo
```

## Configuration

### Environment Variables

Set these environment variables for configuration:

```bash
# Required: Claude API key
export CLAUDE_API_KEY=your-api-key-here

# Optional: Force legacy script mode
export USE_LEGACY_SCRIPTS=true

# Optional: Custom output directory
export MEMORY_BANK_OUTPUT_DIR=/custom/output/path
```

### Legacy Mode

For compatibility with older codebases:

```bash
# Force use of legacy bash scripts
uv run python -m memory_bank_core build /repo --legacy
```

## Output Structure

Each memory bank generates this structure:

```
my-repo_memory_bank/
├── memory-bank/
│   ├── projectbrief.md      # Project overview and goals
│   ├── productContext.md    # User needs and problems
│   ├── systemPatterns.md    # Architecture patterns
│   ├── techContext.md       # Technology stack
│   ├── activeContext.md     # Current development state
│   ├── progress.md          # Implementation status
│   └── tasks/               # Task management
│       ├── _index.md
│       └── [task-files].md
├── logs/                    # Build logs and metadata
└── generation_summary.json  # Build metadata
```

## Practical Examples

### Example 1: Analyze a React Project

```bash
# Navigate to your React project
cd ~/projects/my-react-app

# Generate memory bank
uv run python -m memory_bank_core build . --output-name react-app-analysis

# View results
ls react-app-analysis_memory_bank/memory-bank/
```

### Example 2: Analyze Multiple Projects

```bash
# Set up workspace
mkdir ~/memory-bank-workspace
cd ~/memory-bank-workspace

# Analyze different projects
uv run python -m memory_bank_core build ~/projects/api-service --output-name api-service
uv run python -m memory_bank_core build ~/projects/frontend --output-name frontend  
uv run python -m memory_bank_core build ~/projects/mobile-app --output-name mobile

# List all analyses
uv run python -m memory_bank_core list
```

### Example 3: Background Processing

```bash
# Terminal 1: Start worker
uv run python -m memory_bank_core worker --max-jobs 3

# Terminal 2: Queue multiple jobs
uv run python -m memory_bank_core build ~/project1 --no-wait
uv run python -m memory_bank_core build ~/project2 --no-wait  
uv run python -m memory_bank_core build ~/project3 --no-wait

# Worker processes jobs concurrently
```

### Example 4: Regular Updates

```bash
# Initial analysis
uv run python -m memory_bank_core build ~/my-project --output-name my-project

# After code changes, update the analysis
uv run python -m memory_bank_core update ~/my-project my-project

# Set up as a git hook
echo 'uv run python -m memory_bank_core update . project-analysis' > .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

## Advanced Usage

### Custom Root Directory

```bash
# Create memory banks in specific location
mkdir -p /data/memory-banks
uv run python -m memory_bank_core --root-path /data/memory-banks build ~/project
```

### Batch Processing Script

```bash
#!/bin/bash
# analyze-repos.sh - Batch analyze multiple repositories

REPOS=(
    "/path/to/repo1"
    "/path/to/repo2" 
    "/path/to/repo3"
)

for repo in "${REPOS[@]}"; do
    echo "Analyzing $repo..."
    uv run python -m memory_bank_core build "$repo" --no-wait
done

echo "All jobs queued. Check status with: uv run python -m memory_bank_core list"
```

## Common Issues

### Permission Errors
```bash
# Ensure proper permissions
chmod +x memory_bank_core/main.py
```

### Missing Dependencies
```bash  
# Reinstall dependencies
cd memory_bank_core && uv sync --force
```

### Claude API Issues
```bash
# Verify API key is set
echo $CLAUDE_API_KEY

# Test API connectivity
uv run python -c "import os; print('API Key set:', bool(os.getenv('CLAUDE_API_KEY')))"
```

## Performance Tips

1. **Use Worker Mode**: For multiple projects, start a worker and queue jobs
2. **Custom Output Location**: Use SSD storage for faster I/O
3. **Concurrent Jobs**: Adjust `--max-jobs` based on your system capacity
4. **Incremental Updates**: Use `update` command instead of rebuilding

## Getting Help

```bash
# General help
uv run python -m memory_bank_core --help

# Command-specific help
uv run python -m memory_bank_core build --help
uv run python -m memory_bank_core update --help
uv run python -m memory_bank_core list --help
uv run python -m memory_bank_core worker --help
```

## Next Steps

- Check out [example memory banks](../examples/) to see what gets generated
- Read the [troubleshooting guide](troubleshooting.md) for common issues
- Explore [integration options](integrations.md) for automation