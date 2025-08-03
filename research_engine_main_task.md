# Agent Performance Research System - Main Task

## Overview
Build a comprehensive research engine to compare coding agent performance with and without memory banks. The system will run multiple agents on identical tasks, track metrics, validate outputs independently, and display results in real-time analytics dashboard.

## Core Components

### 1. Research Engine Infrastructure
- Experiment orchestration and management
- Repository isolation and sandbox management  
- Agent abstraction layer for extensibility
- Task generation and management system

### 2. Real-Time UI & Monitoring
- WebSocket-based real-time updates
- Experiment control panel
- Live agent monitoring and metrics
- Results analysis interface

### 3. Validation & Analytics
- Independent validation agent (memory-bank-free)
- Multi-criteria metrics collection (cost, time, quality)
- Statistical ranking and analysis
- Integration with existing dashboard

## Parallel Task Breakdown

This work is divided into **6 parallel tasks** that can be developed independently:

1. **[Task A] Core Infrastructure** (`task_a_core_infrastructure.md`)
2. **[Task B] Agent Integration Layer** (`task_b_agent_integration.md`) 
3. **[Task C] Repository Isolation System** (`task_c_repo_isolation.md`)
4. **[Task D] Real-Time UI Backend** (`task_d_realtime_backend.md`)
5. **[Task E] Frontend Dashboard** (`task_e_frontend_dashboard.md`)
6. **[Task F] Validation & Analytics** (`task_f_validation_analytics.md`)

## Dependencies & Integration Points

### External Dependencies
- Existing memory bank builders (`memory_bank_core/`)
- Cost tracking system (`memory_bank_core/utils/cost_calculator.py`)
- Current FastAPI backend (`backend/`)
- React frontend (`frontend/`)

### Inter-Task Dependencies
- Task C depends on Task A (config models)
- Task B depends on Task A (base interfaces)
- Task D depends on Task A (data models)
- Task F depends on Task A (result models)
- Task E depends on Task D (WebSocket events)

## Success Criteria
- [ ] Multiple agents can run simultaneously on identical tasks
- [ ] Real-time progress monitoring for all running agents
- [ ] Independent validation ranking of agent outputs
- [ ] Cost, time, and quality metrics collection
- [ ] Comparative analytics dashboard
- [ ] Extensible for future agent types

## Timeline
- **Phase 1**: Tasks A, C (Foundation) - Week 1
- **Phase 2**: Tasks B, D (Integration) - Week 2  
- **Phase 3**: Tasks E, F (UI & Analytics) - Week 3
- **Phase 4**: Integration & Testing - Week 4

## Getting Started
1. Read all individual task files for detailed requirements
2. Choose a task based on your expertise and availability
3. Follow the defined interfaces to ensure compatibility
4. Regular sync points for integration testing

## Directory Structure
```
research_engine/
├── core/           # Task A deliverables
├── agents/         # Task B deliverables  
├── isolation/      # Task C deliverables
├── api/           # Task D deliverables
├── frontend/      # Task E deliverables (extends existing)
├── validation/    # Task F deliverables
└── models/        # Shared across Task A
```