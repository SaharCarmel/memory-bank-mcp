from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MemoryBankFile(BaseModel):
    name: str
    path: str
    content: str
    last_modified: datetime
    size: int

class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ChangelogEntry(BaseModel):
    date: str
    title: str
    changes: List[str]
    files_changed: List[str]
    impact: Optional[str] = None

class GenerationSummary(BaseModel):
    generated_at: datetime
    repo_path: str
    files_written: List[str]
    num_messages: int
    method: str

class Graph(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class MemoryBank(BaseModel):
    name: str
    path: str
    files: List[MemoryBankFile]
    tasks: List[Task]
    changelog: List[ChangelogEntry]
    generation_summary: Optional[GenerationSummary] = None
    graph: Optional[Graph] = None
    created_at: datetime
    updated_at: datetime

class MemoryBankSummary(BaseModel):
    name: str
    path: str
    file_count: int
    task_count: int
    last_updated: datetime
    has_changelog: bool

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