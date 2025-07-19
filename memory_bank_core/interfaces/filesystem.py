"""
File system operations interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
from ..models.memory_bank import MemoryBankFile, Task, ChangelogEntry, GenerationSummary, Graph


class FileSystemOperations(ABC):
    """Abstract interface for file system operations"""
    
    @abstractmethod
    async def read_file(self, file_path: Path) -> str:
        """
        Read content from a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string
        """
        pass
    
    @abstractmethod
    async def write_file(self, file_path: Path, content: str) -> None:
        """
        Write content to a file
        
        Args:
            file_path: Path to the file
            content: Content to write
        """
        pass
    
    @abstractmethod
    async def create_directory(self, dir_path: Path) -> None:
        """
        Create a directory and its parents if they don't exist
        
        Args:
            dir_path: Path to the directory
        """
        pass
    
    @abstractmethod
    async def list_files(self, dir_path: Path, pattern: str = "*") -> List[Path]:
        """
        List files in a directory matching a pattern
        
        Args:
            dir_path: Directory to list
            pattern: File pattern to match
            
        Returns:
            List of file paths
        """
        pass
    
    @abstractmethod
    async def parse_memory_bank_files(self, memory_bank_path: Path) -> List[MemoryBankFile]:
        """
        Parse memory bank files from a directory
        
        Args:
            memory_bank_path: Path to memory bank directory
            
        Returns:
            List of memory bank files
        """
        pass
    
    @abstractmethod
    async def parse_tasks(self, tasks_dir: Path) -> List[Task]:
        """
        Parse tasks from a tasks directory
        
        Args:
            tasks_dir: Path to tasks directory
            
        Returns:
            List of tasks
        """
        pass
    
    @abstractmethod
    async def parse_changelog(self, changelog_path: Path) -> List[ChangelogEntry]:
        """
        Parse changelog from a markdown file
        
        Args:
            changelog_path: Path to changelog file
            
        Returns:
            List of changelog entries
        """
        pass
    
    @abstractmethod
    async def parse_generation_summary(self, summary_path: Path) -> Optional[GenerationSummary]:
        """
        Parse generation summary from JSON file
        
        Args:
            summary_path: Path to summary file
            
        Returns:
            GenerationSummary or None if not found
        """
        pass
    
    @abstractmethod
    async def parse_graph(self, graph_path: Path) -> Optional[Graph]:
        """
        Parse graph from JSON file
        
        Args:
            graph_path: Path to graph file
            
        Returns:
            Graph or None if not found
        """
        pass
    
    @abstractmethod
    async def write_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """
        Write data to a JSON file
        
        Args:
            file_path: Path to the JSON file
            data: Data to write
        """
        pass