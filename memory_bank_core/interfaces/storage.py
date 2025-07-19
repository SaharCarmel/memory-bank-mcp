"""
Memory bank storage interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.memory_bank import MemoryBank, MemoryBankSummary


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