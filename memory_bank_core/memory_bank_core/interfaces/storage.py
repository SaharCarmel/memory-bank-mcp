"""
Memory bank storage interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
from ..models.memory_bank import MemoryBank, MemoryBankSummary
from ..models.build_job import BuildJob


class MemoryBankStorage(ABC):
    """Abstract interface for memory bank storage operations"""
    
    @abstractmethod
    async def get_memory_banks(self) -> List[MemoryBankSummary]:
        """
        Get all available memory banks
        
        Returns:
            List of memory bank summaries
        """
        pass
    
    @abstractmethod
    async def get_memory_bank(self, name: str) -> Optional[MemoryBank]:
        """
        Get a specific memory bank by name
        
        Args:
            name: Name of the memory bank
            
        Returns:
            MemoryBank instance or None if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, name: str) -> bool:
        """
        Check if a memory bank exists
        
        Args:
            name: Name of the memory bank
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_memory_bank(self, name: str) -> bool:
        """
        Delete a memory bank
        
        Args:
            name: Name of the memory bank to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_memory_bank_path(self, name: str) -> Optional[str]:
        """
        Get the filesystem path for a memory bank
        
        Args:
            name: Name of the memory bank
            
        Returns:
            Path to the memory bank directory or None if not found
        """
        pass


class JobStorageInterface(ABC):
    """Abstract interface for job storage and logging operations"""
    
    @abstractmethod
    async def save_job_logs(self, job: BuildJob) -> None:
        """
        Save job logs to persistent storage
        
        Args:
            job: BuildJob instance with logs to save
        """
        pass
    
    @abstractmethod
    async def get_log_file_path(self, job: BuildJob) -> Path:
        """
        Generate a log file path for the given job
        
        Args:
            job: BuildJob instance
            
        Returns:
            Path where logs should be saved
        """
        pass
    
    @abstractmethod
    async def load_job_logs(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Load job logs from storage
        
        Args:
            job_id: ID of the job to load logs for
            
        Returns:
            Dictionary with job log data or None if not found
        """
        pass
    
    @abstractmethod
    async def cleanup_old_logs(self, max_age_days: int = 30) -> int:
        """
        Clean up old log files
        
        Args:
            max_age_days: Maximum age in days for log files
            
        Returns:
            Number of files cleaned up
        """
        pass