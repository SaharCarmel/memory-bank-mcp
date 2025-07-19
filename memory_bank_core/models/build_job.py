from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class BuildMode(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"

class BuildConfig(BaseModel):
    repo_path: str
    output_path: str
    mode: BuildMode = BuildMode.FULL
    system_prompt_path: Optional[str] = None
    max_turns: int = 5000

class BuildResult(BaseModel):
    success: bool
    output_path: str
    files_written: List[str]
    metadata: Dict[str, Any]
    errors: List[str] = []

class BuildJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BuildJobType(str, Enum):
    BUILD = "build"
    UPDATE = "update"

class BuildJob(BaseModel):
    id: str
    type: BuildJobType
    status: BuildJobStatus
    repo_path: str
    memory_bank_name: Optional[str] = None
    output_path: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    logs: List[str] = []
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class BuildJobRequest(BaseModel):
    type: BuildJobType
    repo_path: str
    memory_bank_name: Optional[str] = None
    output_name: Optional[str] = None

class BuildJobResponse(BaseModel):
    id: str
    status: BuildJobStatus
    created_at: datetime
    message: str