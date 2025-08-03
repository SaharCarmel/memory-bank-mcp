"""
Claude integration interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

from ...interfaces.builder import BuildProgressCallback


class ClaudeIntegration(ABC):
    """Abstract interface for Claude integration"""
    
    @abstractmethod
    async def execute_build(
        self,
        prompt: str,
        system_prompt: str,
        repo_path: Path,
        progress_callback: Optional[BuildProgressCallback] = None
    ) -> List[str]:
        """
        Execute a memory bank build using Claude
        
        Args:
            prompt: The main prompt for Claude
            system_prompt: System prompt to set context
            repo_path: Path to the repository being analyzed
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of files written during the build process
        """
        pass
    
    @abstractmethod
    async def validate_integration(self) -> bool:
        """
        Validate that the Claude integration is properly configured
        
        Returns:
            True if integration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_allowed_tools(self) -> List[str]:
        """
        Get the list of tools allowed for Claude operations
        
        Returns:
            List of tool names
        """
        pass
    
    @abstractmethod
    def configure_options(self, **kwargs) -> Dict[str, Any]:
        """
        Configure options for Claude execution
        
        Args:
            **kwargs: Configuration options
            
        Returns:
            Dictionary of configured options
        """
        pass