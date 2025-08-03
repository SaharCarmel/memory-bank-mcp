"""
Legacy backward compatibility layer for memory bank operations
Supports fallback to bash scripts during migration period
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class LegacyScriptExecutor:
    """
    Provides fallback to bash scripts for memory bank operations
    Can be enabled via environment variable: USE_LEGACY_SCRIPTS=true
    """
    
    def __init__(self, root_path: Path, scripts_path: Optional[Path] = None):
        """
        Initialize the legacy script executor
        
        Args:
            root_path: Root path where memory banks are stored
            scripts_path: Path to legacy scripts (defaults to root_path)
        """
        self.root_path = Path(root_path)
        self.scripts_path = scripts_path or self.root_path
    
    @staticmethod
    def is_enabled() -> bool:
        """Check if legacy mode is enabled via environment variable"""
        return os.getenv("USE_LEGACY_SCRIPTS", "false").lower() == "true"
    
    async def execute_legacy_build(
        self,
        repo_path: str,
        output_name: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute build using legacy bash script
        
        Args:
            repo_path: Path to the repository
            output_name: Name for the output directory
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with build results
            
        Raises:
            FileNotFoundError: If the legacy script is not found
            subprocess.CalledProcessError: If the script fails
        """
        build_script = self.scripts_path / "build_memory_bank.sh"
        
        if not build_script.exists():
            raise FileNotFoundError(f"Legacy build script not found: {build_script}")
        
        if progress_callback:
            await self._call_progress_callback(progress_callback, "Using legacy bash script mode (USE_LEGACY_SCRIPTS=true)")
        
        cmd = ["bash", str(build_script), repo_path, output_name]
        
        if progress_callback:
            await self._call_progress_callback(progress_callback, f"[LEGACY MODE] Executing: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd,
            cwd=str(self.root_path),
            capture_output=True,
            text=True
        )
        
        # Log output through progress callback if available
        if process.stdout and progress_callback:
            for line in process.stdout.strip().split('\n'):
                if line.strip():
                    await self._call_progress_callback(progress_callback, f"LEGACY_BUILD: {line}")
        
        if process.stderr and progress_callback:
            for line in process.stderr.strip().split('\n'):
                if line.strip():
                    await self._call_progress_callback(progress_callback, f"LEGACY_BUILD_ERR: {line}")
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, 
                cmd, 
                f"Legacy script failed with return code {process.returncode}"
            )
        
        return {
            "success": True,
            "output_path": str(self.root_path / output_name),
            "files_written": [],  # Legacy scripts don't track individual files
            "metadata": {
                "mode": "legacy_bash_script",
                "script_used": str(build_script)
            },
            "errors": []
        }
    
    async def execute_legacy_update(
        self,
        repo_path: str,
        memory_bank_name: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute update using legacy bash script
        
        Args:
            repo_path: Path to the repository
            memory_bank_name: Name of the memory bank to update
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with update results
            
        Raises:
            FileNotFoundError: If the legacy script is not found
            subprocess.CalledProcessError: If the script fails
        """
        update_script = self.scripts_path / "update_memory_bank.sh"
        
        if not update_script.exists():
            raise FileNotFoundError(f"Legacy update script not found: {update_script}")
        
        if progress_callback:
            await self._call_progress_callback(progress_callback, "Using legacy bash script mode (USE_LEGACY_SCRIPTS=true)")
        
        cmd = ["bash", str(update_script), repo_path, memory_bank_name]
        
        if progress_callback:
            await self._call_progress_callback(progress_callback, f"[LEGACY MODE] Executing: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd,
            cwd=str(self.root_path),
            capture_output=True,
            text=True
        )
        
        # Log output through progress callback if available
        if process.stdout and progress_callback:
            for line in process.stdout.strip().split('\n'):
                if line.strip():
                    await self._call_progress_callback(progress_callback, f"LEGACY_UPDATE: {line}")
        
        if process.stderr and progress_callback:
            for line in process.stderr.strip().split('\n'):
                if line.strip():
                    await self._call_progress_callback(progress_callback, f"LEGACY_UPDATE_ERR: {line}")
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, 
                cmd, 
                f"Legacy script failed with return code {process.returncode}"
            )
        
        return {
            "success": True,
            "output_path": str(self.root_path / memory_bank_name),
            "files_written": [],  # Legacy scripts don't track individual files
            "metadata": {
                "mode": "legacy_bash_script", 
                "script_used": str(update_script),
                "memory_bank_name": memory_bank_name
            },
            "errors": []
        }
    
    async def _call_progress_callback(self, progress_callback: Optional[Callable], message: str):
        """Helper to handle both sync and async progress callbacks"""
        if progress_callback:
            import asyncio
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(message)
            else:
                progress_callback(message)


# Backward compatibility: keep the old class name and interface
class BackwardCompatibilityMode:
    """
    DEPRECATED: Use LegacyScriptExecutor instead
    Maintains backward compatibility with existing backend code
    """
    
    @staticmethod
    def is_enabled() -> bool:
        """Check if backward compatibility mode is enabled"""
        return LegacyScriptExecutor.is_enabled()
    
    @staticmethod
    async def execute_legacy_build(
        root_path: Path,
        repo_path: str,
        output_name: str,
        logs: List[str]
    ) -> dict:
        """Execute build using legacy bash script (compatibility wrapper)"""
        executor = LegacyScriptExecutor(root_path)
        
        # Create a progress callback that appends to logs
        async def log_callback(message: str):
            logs.append(message)
        
        result = await executor.execute_legacy_build(
            repo_path=repo_path,
            output_name=output_name,
            progress_callback=log_callback
        )
        
        # Return in the old format for compatibility
        return {
            "success": result["success"],
            "output_path": result["output_path"],
            "mode": result["metadata"]["mode"]
        }
    
    @staticmethod
    async def execute_legacy_update(
        root_path: Path,
        repo_path: str,
        memory_bank_name: str,
        logs: List[str]
    ) -> dict:
        """Execute update using legacy bash script (compatibility wrapper)"""
        executor = LegacyScriptExecutor(root_path)
        
        # Create a progress callback that appends to logs
        async def log_callback(message: str):
            logs.append(message)
        
        result = await executor.execute_legacy_update(
            repo_path=repo_path,
            memory_bank_name=memory_bank_name,
            progress_callback=log_callback
        )
        
        # Return in the old format for compatibility
        return {
            "success": result["success"],
            "memory_bank_name": memory_bank_name,
            "mode": result["metadata"]["mode"]
        }
