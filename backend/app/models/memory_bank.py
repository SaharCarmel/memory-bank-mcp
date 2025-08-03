# Import models from the core module
from memory_bank_core.models.memory_bank import (
    MemoryBankFile,
    Task, 
    ChangelogEntry,
    GenerationSummary,
    Graph,
    MemoryBank,
    MemoryBankSummary
)

from memory_bank_core.models.build_job import (
    BuildJobStatus,
    BuildJobType,
    BuildJob,
    BuildJobRequest,
    BuildJobResponse,
    BuildConfig,
    BuildResult,
    BuildMode
)

# Re-export for backward compatibility
__all__ = [
    "MemoryBankFile",
    "Task", 
    "ChangelogEntry",
    "GenerationSummary",
    "Graph",
    "MemoryBank",
    "MemoryBankSummary",
    "BuildJobStatus",
    "BuildJobType", 
    "BuildJob",
    "BuildJobRequest",
    "BuildJobResponse",
    "BuildConfig",
    "BuildResult",
    "BuildMode"
]