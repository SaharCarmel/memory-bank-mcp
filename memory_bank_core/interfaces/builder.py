"""
Memory bank builder interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
from pathlib import Path

# Type alias for progress callback
BuildProgressCallback = Callable[[str], Awaitable[None]]


class MemoryBankBuilder(ABC):
    """Abstract interface for memory bank builders"""
    
    @abstractmethod
    async def build_memory_bank(
        self,
        repo_path: str,
        output_name: Optional[str] = None,
        progress_callback: Optional[BuildProgressCallback] = None
    ) -> Dict[str, Any]:
        """
        Build a memory bank for the given repository
        
        Args:
            repo_path: Path to the repository to analyze
            output_name: Optional custom name for the output directory
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with build results including:
            - success: bool
            - output_path: str
            - files_written: List[str]
            - mode: str (full_build, incremental_update)
            - timestamp: str
        """
        pass
    
    @abstractmethod
    async def update_memory_bank(
        self,
        repo_path: str,
        memory_bank_name: str,
        progress_callback: Optional[BuildProgressCallback] = None
    ) -> Dict[str, Any]:
        """
        Update an existing memory bank
        
        Args:
            repo_path: Path to the repository
            memory_bank_name: Name of the memory bank to update
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with update results
        """
        pass
    
    @abstractmethod
    def validate_repository(self, repo_path: str) -> bool:
        """
        Validate that the repository path is valid for memory bank creation
        
        Args:
            repo_path: Path to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass