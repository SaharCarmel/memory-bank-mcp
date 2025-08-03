"""
Memory Bank Builder Service
Backend adapter for the core memory bank building module
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from core import CoreMemoryBankBuilder, BuildConfig, BuildResult, BuildMode

logger = logging.getLogger(__name__)


class MemoryBankBuilder:
    """Backend adapter for core memory bank building"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.core_builder = CoreMemoryBankBuilder(root_path)
        
    async def build_memory_bank(
        self, 
        repo_path: str, 
        output_name: Optional[str] = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Build a memory bank for the given repository
        
        Args:
            repo_path: Path to the repository to analyze
            output_name: Optional custom name for the output directory
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with build results
        """
        # Determine output path
        if output_name:
            output_path = self.root_path / output_name
        else:
            repo_name = Path(repo_path).name or "repo"
            output_path = self.root_path / f"{repo_name}_memory_bank"
            
        # Create build configuration
        config = BuildConfig(
            repo_path=repo_path,
            output_path=str(output_path),
            mode=BuildMode.FULL,
            system_prompt_path=str(self.root_path / "system_prompt.md"),
            max_turns=5000
        )
        
        # Use the core builder
        result = await self.core_builder.build_memory_bank(
            config=config,
            progress_callback=progress_callback
        )
        
        # Convert BuildResult to the expected dictionary format for backward compatibility
        return {
            "success": result.success,
            "output_path": result.output_path,
            "files_written": result.files_written,
            "metadata": result.metadata,
            "errors": result.errors
        }
    
    async def update_memory_bank(
        self,
        repo_path: str,
        memory_bank_name: str,
        progress_callback=None
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
        # Determine output path for existing memory bank
        output_path = self.root_path / memory_bank_name
        
        # Create build configuration for incremental update
        config = BuildConfig(
            repo_path=repo_path,
            output_path=str(output_path),
            mode=BuildMode.INCREMENTAL,
            system_prompt_path=str(self.root_path / "system_prompt.md"),
            max_turns=5000
        )
        
        # Use the core builder
        result = await self.core_builder.build_memory_bank(
            config=config,
            progress_callback=progress_callback
        )
        
        # Convert BuildResult to the expected dictionary format for backward compatibility
        return {
            "success": result.success,
            "output_path": result.output_path,
            "files_written": result.files_written,
            "metadata": result.metadata,
            "errors": result.errors
        }