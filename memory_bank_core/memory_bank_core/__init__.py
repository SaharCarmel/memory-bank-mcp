"""
Memory Bank Core Module

Extracted memory bank building logic for reuse across different interfaces.
"""

# Core builders (optional - requires claude_code_sdk)
try:
    from .builders.core_builder import CoreMemoryBankBuilder
    _HAS_CLAUDE_SDK = True
except ImportError:
    CoreMemoryBankBuilder = None
    _HAS_CLAUDE_SDK = False

# Models
from .models.memory_bank import MemoryBank, MemoryBankSummary
from .models.build_job import (
    BuildConfig, 
    BuildResult, 
    BuildMode, 
    BuildJob, 
    BuildJobStatus, 
    BuildJobType, 
    BuildJobRequest,
    BuildJobResponse
)

# Services
from .services.job_manager import JobManager, DefaultJobStorageAdapter

# Interfaces
from .interfaces.storage import MemoryBankStorage, JobStorageInterface
from .interfaces.validation import JobValidationInterface, DefaultJobValidator

# Integrations
from .integrations.legacy import LegacyScriptExecutor, BackwardCompatibilityMode

__version__ = "1.0.0"

# Build the exports list dynamically based on available dependencies
_all_exports = [
    # Models
    "MemoryBank", 
    "MemoryBankSummary",
    "BuildConfig",
    "BuildResult", 
    "BuildMode",
    "BuildJob",
    "BuildJobStatus",
    "BuildJobType",
    "BuildJobRequest", 
    "BuildJobResponse",
    
    # Services
    "JobManager",
    "DefaultJobStorageAdapter",
    
    # Interfaces
    "MemoryBankStorage",
    "JobStorageInterface", 
    "JobValidationInterface",
    "DefaultJobValidator",
    
    # Integrations
    "LegacyScriptExecutor",
    "BackwardCompatibilityMode"
]

# Add core builder if available
if _HAS_CLAUDE_SDK:
    _all_exports.insert(0, "CoreMemoryBankBuilder")

__all__ = _all_exports