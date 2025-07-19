"""
Memory Bank Core Module

Extracted memory bank building logic for reuse across different interfaces.
"""

from .builders.core_builder import CoreMemoryBankBuilder
from .models.memory_bank import MemoryBank, MemoryBankSummary
from .models.build_job import BuildConfig, BuildResult, BuildMode

__version__ = "1.0.0"

__all__ = [
    "CoreMemoryBankBuilder",
    "MemoryBank", 
    "MemoryBankSummary",
    "BuildConfig",
    "BuildResult", 
    "BuildMode"
]