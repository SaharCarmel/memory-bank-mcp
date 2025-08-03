# Task D: Real-Time Backend API

## Objective
Build WebSocket-based real-time backend system for experiment management, agent monitoring, and live metrics streaming.

## Deliverables

### 1. WebSocket Handler (`research_engine/api/websocket_handler.py`)
- Real-time experiment progress streaming
- Agent status and metrics broadcasting
- Client connection management
- Event routing and filtering

### 2. API Routes (`research_engine/api/routes.py`)
- Experiment CRUD operations
- Agent management endpoints
- Results querying and export
- Configuration management

### 3. Event System (`research_engine/api/events.py`)
- Event serialization and broadcasting
- Event filtering and subscriptions
- Rate limiting and throttling
- Event persistence for replay

### 4. Backend Integration (`research_engine/api/integration.py`)
- Integration with existing FastAPI backend
- Authentication and authorization
- CORS configuration for research UI
- API versioning and documentation

## Interface Contracts

### WebSocket Events
```python
class WebSocketEvent:
    event_type: str  # "experiment_started", "agent_progress", "run_completed"
    experiment_id: str
    data: Dict[str, Any]
    timestamp: datetime
    
# Event Types:
# - experiment_created, experiment_started, experiment_completed
# - agent_initialized, agent_progress, agent_completed, agent_failed
# - metrics_updated, validation_completed
# - system_status, error_occurred
```

### API Endpoints
```python
# Experiment Management
POST   /api/research/experiments          # Create experiment
GET    /api/research/experiments          # List experiments
GET    /api/research/experiments/{id}     # Get experiment details
POST   /api/research/experiments/{id}/start   # Start experiment
POST   /api/research/experiments/{id}/stop    # Stop experiment
DELETE /api/research/experiments/{id}     # Delete experiment

# Agent Management
GET    /api/research/agents               # List available agents
GET    /api/research/agents/{run_id}      # Get agent run details
POST   /api/research/agents/{run_id}/stop # Stop agent run

# Results and Analytics
GET    /api/research/results/{experiment_id}  # Get experiment results
GET    /api/research/metrics/{experiment_id}  # Get experiment metrics
POST   /api/research/export/{experiment_id}   # Export results

# System Status
GET    /api/research/status               # System health and stats
GET    /api/research/config               # Get configuration
POST   /api/research/config               # Update configuration
```

### WebSocket Connection Interface
```python
class WebSocketManager:
    async def connect(self, websocket: WebSocket, experiment_id: Optional[str] = None)
    async def disconnect(self, websocket: WebSocket)
    async def broadcast_event(self, event: WebSocketEvent)
    async def send_to_experiment(self, experiment_id: str, event: WebSocketEvent)
```

## Dependencies
- **Task A**: `Experiment`, `AgentRun`, `ExperimentEvent` models
- **External**: `fastapi`, `websockets`, `asyncio`
- **Internal**: Existing FastAPI backend structure

## Testing Requirements
- WebSocket connection and messaging tests
- API endpoint functionality tests
- Event broadcasting and filtering tests
- Authentication and authorization tests
- Load testing for concurrent connections

## Integration Points
- **Task A**: Consumes experiment events and data models
- **Task B**: Receives agent progress events
- **Task E**: Provides WebSocket events and API endpoints
- **Internal**: Extends existing FastAPI backend

## Success Criteria
- [ ] Real-time WebSocket event streaming
- [ ] Complete experiment management API
- [ ] Agent monitoring and control endpoints
- [ ] Results querying and export functionality
- [ ] Integration with existing backend authentication
- [ ] Comprehensive API documentation
- [ ] Load testing for multiple concurrent experiments

## Files to Create/Modify
```
research_engine/api/
├── __init__.py
├── websocket_handler.py
├── routes.py
├── events.py
├── integration.py
└── tests/
    ├── test_websocket.py
    ├── test_routes.py
    └── test_integration.py

# Modify existing backend
backend/app/api/routes.py  # Add research routes
backend/main.py           # Include research API
```

## WebSocket Event Examples
```python
# Experiment started
{
    "event_type": "experiment_started",
    "experiment_id": "exp_123",
    "data": {
        "name": "Memory Bank Comparison",
        "total_agents": 8,
        "config": {...}
    },
    "timestamp": "2025-01-26T10:00:00Z"
}

# Agent progress
{
    "event_type": "agent_progress", 
    "experiment_id": "exp_123",
    "data": {
        "run_id": "run_456",
        "agent_type": "claude_code",
        "progress_percent": 45.0,
        "current_action": "Implementing user authentication",
        "metrics": {
            "tokens_used": 15000,
            "cost": 0.75,
            "elapsed_time": 300
        }
    },
    "timestamp": "2025-01-26T10:05:00Z"
}
```

## Implementation Notes
- Use FastAPI's WebSocket support
- Implement connection pooling for scalability
- Add proper error handling and reconnection logic
- Include rate limiting to prevent abuse
- Design for horizontal scaling with Redis (future)
- Follow existing backend patterns and conventions

## Progress
- [ ] Implement WebSocket Handler (websocket_handler.py)
- [ ] Create API Routes (routes.py)  
- [ ] Build Event System (events.py)
- [ ] Backend Integration (integration.py)
- [ ] Create comprehensive tests for all components
- [ ] Integration with existing FastAPI backend