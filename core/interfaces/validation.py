"""
Validation interfaces for memory bank operations
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.build_job import BuildJobRequest, BuildJobType


class JobValidationInterface(ABC):
    """Abstract interface for job validation operations"""
    
    @abstractmethod
    async def validate_build_request(self, request: BuildJobRequest) -> None:
        """
        Validate a build job request
        
        Args:
            request: BuildJobRequest to validate
            
        Raises:
            ValueError: If the request is invalid
        """
        pass
    
    @abstractmethod
    async def validate_repository_path(self, repo_path: str) -> None:
        """
        Validate that a repository path exists and is accessible
        
        Args:
            repo_path: Path to the repository
            
        Raises:
            ValueError: If the repository path is invalid
        """
        pass
    
    @abstractmethod
    async def validate_memory_bank_exists(self, memory_bank_name: str) -> None:
        """
        Validate that a memory bank exists (for update operations)
        
        Args:
            memory_bank_name: Name of the memory bank
            
        Raises:
            ValueError: If the memory bank doesn't exist
        """
        pass
    
    @abstractmethod
    async def check_concurrent_jobs_limit(self, max_concurrent: int = 3) -> None:
        """
        Check if the number of running jobs is within limits
        
        Args:
            max_concurrent: Maximum number of concurrent jobs allowed
            
        Raises:
            ValueError: If too many jobs are running
        """
        pass
    
    @abstractmethod
    async def validate_output_permissions(self, output_path: str) -> None:
        """
        Validate that the output path is writable
        
        Args:
            output_path: Path where output will be written
            
        Raises:
            ValueError: If the output path is not writable
        """
        pass


class DefaultJobValidator(JobValidationInterface):
    """Default implementation of job validation"""
    
    def __init__(self, root_path: str, get_running_jobs_count_func=None):
        """
        Initialize the validator
        
        Args:
            root_path: Root path for memory banks
            get_running_jobs_count_func: Function to get count of running jobs
        """
        self.root_path = root_path
        self.get_running_jobs_count = get_running_jobs_count_func
    
    async def validate_build_request(self, request: BuildJobRequest) -> None:
        """Validate a build job request"""
        # Validate repository path
        await self.validate_repository_path(request.repo_path)
        
        # For update operations, validate memory bank exists
        if request.type == BuildJobType.UPDATE:
            if not request.memory_bank_name:
                raise ValueError("Memory bank name is required for update operations")
            await self.validate_memory_bank_exists(request.memory_bank_name)
        
        # Check concurrent jobs limit
        await self.check_concurrent_jobs_limit()
    
    async def validate_repository_path(self, repo_path: str) -> None:
        """Validate repository path exists"""
        import os
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path is not a directory: {repo_path}")
    
    async def validate_memory_bank_exists(self, memory_bank_name: str) -> None:
        """Validate memory bank exists"""
        from pathlib import Path
        memory_bank_path = Path(self.root_path) / memory_bank_name
        if not memory_bank_path.exists():
            raise ValueError(f"Memory bank does not exist: {memory_bank_name}")
    
    async def check_concurrent_jobs_limit(self, max_concurrent: int = 3) -> None:
        """Check concurrent jobs limit"""
        if self.get_running_jobs_count:
            running_jobs = self.get_running_jobs_count()
            if running_jobs >= max_concurrent:
                raise ValueError("Too many jobs are currently running. Please wait for some to complete.")
    
    async def validate_output_permissions(self, output_path: str) -> None:
        """Validate output path is writable"""
        from pathlib import Path
        import os
        
        output_dir = Path(output_path)
        
        # Check if parent directory exists and is writable
        if output_dir.exists():
            if not os.access(output_dir, os.W_OK):
                raise ValueError(f"Output path is not writable: {output_path}")
        else:
            # Check if parent directory is writable
            parent = output_dir.parent
            if not parent.exists():
                # Try to create parent directories
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    raise ValueError(f"Cannot create output directory: {output_path}")
            elif not os.access(parent, os.W_OK):
                raise ValueError(f"Parent directory is not writable: {parent}")