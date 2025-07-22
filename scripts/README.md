# Scripts Directory

This directory contains utility scripts for the PC Cortex Memory Bank system.

## System Scripts
- **start_dashboard.sh** - Starts the web dashboard (frontend and backend)
- **start_system.sh** - Starts the complete system including MCP server

## Cost Analysis Scripts
- **analyze_memory_bank_costs.py** - Analyze historical costs from Claude Code sessions
- **get_build_cost.py** - Get cost for a specific build by timestamp
- **cost_demo.py** - Interactive cost demonstration and model comparisons

## Development & Testing
- **debug_sessions.py** - Debug session detection and parsing
- **test_cost_integration.py** - Integration test for cost tracking system

## Usage

### Start the Dashboard
```bash
./scripts/start_dashboard.sh
```
The dashboard will open at http://localhost:5174

### Analyze Build Costs
```bash
# Analyze all memory bank sessions for this project
python scripts/analyze_memory_bank_costs.py "/path/to/project"

# Get cost for specific build
python scripts/get_build_cost.py test_output/full_multi_agent_20250723_014644/

# See cost demonstrations
python scripts/cost_demo.py
```