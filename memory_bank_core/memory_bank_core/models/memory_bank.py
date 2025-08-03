from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

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