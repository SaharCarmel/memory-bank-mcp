# CLI Integration Implementation

This document describes the implementation of CLI integration for the Memory Bank Dashboard, allowing users to trigger memory bank builds directly from the web interface.

## Overview

The CLI integration consists of:
1. **Backend API**: RESTful endpoints for managing build jobs
2. **Background Job Processing**: Asynchronous job queue with worker
3. **Frontend Interface**: React components for triggering and monitoring builds
4. **Real-time Updates**: Polling-based status updates

## Architecture

### Backend Components

#### 1. Data Models (`app/models/memory_bank.py`)
- **BuildJobStatus**: Enum for job states (pending, running, completed, failed, cancelled)
- **BuildJobType**: Enum for operation types (build, update)
- **BuildJob**: Complete job information with logs and timestamps
- **BuildJobRequest**: Request payload for creating jobs
- **BuildJobResponse**: Response payload for job creation

#### 2. Build Job Service (`app/services/build_job_service.py`)
- **Job Management**: Create, track, and cancel jobs
- **Background Worker**: Async worker loop processing jobs from queue
- **CLI Execution**: Executes shell scripts (`build_memory_bank.sh`, `update_memory_bank.sh`)
- **Validation**: Validates repository paths and memory bank existence
- **Concurrency Control**: Limits concurrent jobs to prevent resource exhaustion

#### 3. API Endpoints (`app/api/routes.py`)
- `POST /builds` - Create new build job
- `GET /builds` - List all build jobs
- `GET /builds/{id}` - Get specific build job
- `GET /builds/{id}/status` - Get job status with recent logs
- `POST /builds/{id}/cancel` - Cancel pending job

### Frontend Components

#### 1. API Service (`services/api.js`)
- **Build Job Methods**: CRUD operations for build jobs
- **Error Handling**: Proper error message extraction
- **HTTP Client**: Fetch-based API communication

#### 2. Build Panel Component (`components/BuildPanel.js`)
- **Job Creation Form**: Form for configuring build jobs
- **Job Status Display**: Real-time job status visualization
- **Log Viewer**: Recent log lines for active jobs
- **Auto-refresh**: Polling every 2 seconds for status updates

#### 3. Dashboard Integration (`components/Dashboard.js`)
- **Unified Interface**: Build panel integrated into main dashboard
- **Layout**: Build jobs displayed prominently above memory banks list

## Usage

### Creating a Build Job

1. Click "New Build Job" in the dashboard
2. Select job type:
   - **Build**: Create new memory bank from repository
   - **Update**: Update existing memory bank with changes
3. Enter repository path (absolute path required)
4. For build jobs: optionally specify output name
5. For update jobs: specify existing memory bank name
6. Click "Create Job"

### Monitoring Jobs

- Jobs are displayed in real-time with status indicators
- Color-coded status: yellow (pending), blue (running), green (completed), red (failed)
- Recent log lines shown for active jobs
- Full job details available by clicking on job cards

### Job Status Flow

1. **Pending**: Job created and queued
2. **Running**: Job being processed by worker
3. **Completed**: Job finished successfully
4. **Failed**: Job encountered an error
5. **Cancelled**: Job was cancelled before completion

## Implementation Details

### Background Job Processing

The system uses an async job queue with a single worker to process jobs sequentially:

```python
# Job creation adds to queue
await self.job_queue.put(job_id)

# Worker processes jobs
async def _worker_loop(self):
    while self.running:
        job_id = await self.job_queue.get()
        await self._process_job(job_id)
```

### CLI Command Execution

Jobs execute the existing shell scripts:

```bash
# Build job
./build_memory_bank.sh /path/to/repo output_name

# Update job
./update_memory_bank.sh /path/to/repo memory_bank_name
```

### Error Handling

- **Request Validation**: Repository paths and memory bank existence checked
- **Concurrency Limits**: Maximum 3 concurrent jobs
- **Process Monitoring**: Command output captured and stored in job logs
- **Error Recovery**: Failed jobs marked with error messages

### Real-time Updates

Frontend polls the backend every 2 seconds for job status updates:

```javascript
useEffect(() => {
  const interval = setInterval(loadBuildJobs, 2000);
  return () => clearInterval(interval);
}, []);
```

## API Reference

### Create Build Job
```bash
POST /api/builds
{
  "type": "build",
  "repo_path": "/path/to/repository",
  "output_name": "my_memory_bank"
}
```

### Get Job Status
```bash
GET /api/builds/{job_id}/status
{
  "id": "job_id",
  "status": "running",
  "progress": {
    "created_at": "2023-...",
    "started_at": "2023-...",
    "logs": ["Recent log lines..."]
  }
}
```

## Configuration

### Environment Variables
- `CORS_ORIGINS`: Allowed origins for CORS (default: localhost:3333)
- `API_PORT`: Backend server port (default: 8888)
- `FRONTEND_PORT`: Frontend development server port (default: 3333)

### Concurrency Settings
- Maximum concurrent jobs: 3 (configurable in `BuildJobService`)
- Polling interval: 2 seconds (configurable in `BuildPanel`)

## Testing

The implementation includes comprehensive validation:
- Repository path existence checks
- Memory bank validation for update operations
- Concurrency limits enforcement
- Proper error handling and logging

## Future Enhancements

1. **WebSocket Integration**: Real-time updates instead of polling
2. **Job Persistence**: Store jobs in database for restart recovery
3. **Advanced Logging**: Structured logging with log levels
4. **Job Scheduling**: Cron-like scheduling for recurring builds
5. **Parallel Processing**: Multiple workers for concurrent job execution

## Files Modified/Created

### Backend
- `app/models/memory_bank.py` - Added build job models
- `app/services/build_job_service.py` - New service for job management
- `app/api/routes.py` - Added build job endpoints
- `main.py` - Added worker lifecycle management

### Frontend
- `services/api.js` - Added build job API methods
- `components/BuildPanel.js` - New build job management component
- `components/Dashboard.js` - Integrated build panel

### Documentation
- `README_CLI_Integration.md` - This documentation file