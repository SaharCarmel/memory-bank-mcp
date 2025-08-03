"""Experiment-wide memory bank management for research workflows."""

import asyncio
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExperimentMemoryBank(BaseModel):
    """Represents a pre-built memory bank for an entire experiment."""
    
    experiment_id: str = Field(..., description="Experiment identifier")
    repo_url: str = Field(..., description="Source repository URL")
    memory_bank_path: Path = Field(..., description="Path to built memory bank")
    created_at: datetime = Field(default_factory=datetime.now, description="When memory bank was built")
    build_time_seconds: float = Field(..., description="Time taken to build memory bank")
    files_count: int = Field(..., description="Number of files in memory bank")
    total_size_bytes: int = Field(..., description="Total size of memory bank")
    repo_commit_hash: Optional[str] = Field(None, description="Git commit hash of source repo")
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def total_size_mb(self) -> float:
        """Total size in MB."""
        return self.total_size_bytes / (1024 * 1024)
    
    def is_valid(self) -> bool:
        """Check if memory bank is still valid (directory exists)."""
        return self.memory_bank_path.exists() and self.memory_bank_path.is_dir()


class ExperimentMemoryBankManager:
    """Manages memory banks at the experiment level for efficient reuse."""
    
    def __init__(self, base_memory_bank_dir: Optional[Path] = None):
        """Initialize experiment memory bank manager.
        
        Args:
            base_memory_bank_dir: Base directory for storing experiment memory banks
        """
        self.base_memory_bank_dir = base_memory_bank_dir or Path(tempfile.gettempdir()) / "experiment_memory_banks"
        self.active_memory_banks: Dict[str, ExperimentMemoryBank] = {}
        
        # Ensure base directory exists
        self.base_memory_bank_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ExperimentMemoryBankManager initialized with base directory: {self.base_memory_bank_dir}")
    
    async def build_memory_bank(
        self,
        experiment_id: str,
        repo_url: str,
        force_rebuild: bool = False,
        build_timeout_minutes: int = 10,
        progress_callback: Optional[callable] = None
    ) -> ExperimentMemoryBank:
        """Build a memory bank for an entire experiment.
        
        Args:
            experiment_id: Unique experiment identifier
            repo_url: Git repository URL to build memory bank for
            force_rebuild: Whether to rebuild if memory bank already exists
            build_timeout_minutes: Timeout for memory bank building
            
        Returns:
            ExperimentMemoryBank with built memory bank information
            
        Raises:
            RuntimeError: If memory bank build fails
        """
        # Check if we already have a valid memory bank for this experiment
        if not force_rebuild and experiment_id in self.active_memory_banks:
            existing_mb = self.active_memory_banks[experiment_id]
            if existing_mb.is_valid():
                logger.info(f"Using existing memory bank for experiment {experiment_id}")
                return existing_mb
            else:
                logger.warning(f"Existing memory bank for {experiment_id} is invalid, rebuilding")
        
        start_time = datetime.now()
        logger.info(f"Building memory bank for experiment {experiment_id} with repo {repo_url}")
        
        if progress_callback:
            progress_callback(f"Starting memory bank build for experiment {experiment_id}")
        
        try:
            # Create experiment-specific directory
            experiment_dir = self.base_memory_bank_dir / experiment_id
            experiment_dir.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                progress_callback(f"Cloning repository {repo_url}...")
            
            # Clone repository to temporary location
            temp_repo_path = experiment_dir / "temp_repo"
            if temp_repo_path.exists():
                shutil.rmtree(temp_repo_path)
            
            await self._clone_repository(repo_url, temp_repo_path)
            logger.info(f"Repository cloned to {temp_repo_path}")
            
            if progress_callback:
                progress_callback("Repository cloned successfully, analyzing commit...")
            
            # Get commit hash for tracking
            commit_hash = await self._get_commit_hash(temp_repo_path)
            
            if progress_callback:
                progress_callback(f"Starting multi-agent memory bank build (commit: {commit_hash[:8] if commit_hash else 'unknown'})...")
            
            # Build memory bank
            memory_bank_path = experiment_dir / "memory-bank"
            if memory_bank_path.exists():
                shutil.rmtree(memory_bank_path)
            
            build_result = await self._build_memory_bank_from_repo(
                repo_path=temp_repo_path,
                output_path=memory_bank_path,
                timeout_minutes=build_timeout_minutes,
                progress_callback=progress_callback
            )
            
            # Clean up temporary repo
            shutil.rmtree(temp_repo_path)
            
            if not build_result["success"]:
                raise RuntimeError(f"Memory bank build failed: {build_result['error']}")
            
            if progress_callback:
                progress_callback("Memory bank build completed, calculating statistics...")
            
            # Get memory bank statistics
            files_count, total_size = await self._get_directory_stats(memory_bank_path)
            build_time = (datetime.now() - start_time).total_seconds()
            
            # Create experiment memory bank object
            experiment_memory_bank = ExperimentMemoryBank(
                experiment_id=experiment_id,
                repo_url=repo_url,
                memory_bank_path=memory_bank_path,
                build_time_seconds=build_time,
                files_count=files_count,
                total_size_bytes=total_size,
                repo_commit_hash=commit_hash
            )
            
            # Store in active memory banks
            self.active_memory_banks[experiment_id] = experiment_memory_bank
            
            logger.info(f"Memory bank built successfully for experiment {experiment_id}")
            logger.info(f"  • Files: {files_count}, Size: {experiment_memory_bank.total_size_mb:.1f}MB")
            logger.info(f"  • Build time: {build_time:.1f}s, Commit: {commit_hash[:8] if commit_hash else 'unknown'}")
            
            return experiment_memory_bank
            
        except Exception as e:
            logger.error(f"Failed to build memory bank for experiment {experiment_id}: {e}")
            raise RuntimeError(f"Memory bank build failed: {e}")
    
    async def _clone_repository(self, repo_url: str, target_path: Path) -> None:
        """Clone git repository to target path."""
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            process = await asyncio.create_subprocess_exec(
                'git', 'clone', '--depth', '1', repo_url, str(target_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown git error"
                raise RuntimeError(f"Git clone failed: {error_msg}")
                
        except FileNotFoundError:
            raise RuntimeError("Git command not found. Please ensure git is installed.")
        except Exception as e:
            raise RuntimeError(f"Repository cloning failed: {e}")
    
    async def _get_commit_hash(self, repo_path: Path) -> Optional[str]:
        """Get the current commit hash of a repository."""
        try:
            process = await asyncio.create_subprocess_exec(
                'git', 'rev-parse', 'HEAD',
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                logger.warning("Could not get commit hash")
                return None
                
        except Exception as e:
            logger.warning(f"Error getting commit hash: {e}")
            return None
    
    async def _build_memory_bank_from_repo(
        self,
        repo_path: Path,
        output_path: Path,
        timeout_minutes: int,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Build memory bank from cloned repository."""
        try:
            # Import memory bank builder - use relative path to local memory_bank_core
            import sys
            project_root = Path(__file__).parent.parent.parent  # Go up to project root
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            from memory_bank_core.builders.multi_agent_builder import MultiAgentMemoryBankBuilder
            from memory_bank_core.models.build_job import BuildConfig, BuildMode
            
            # Create build configuration using the correct API
            build_config = BuildConfig(
                repo_path=str(repo_path),
                output_path=str(output_path),
                mode=BuildMode.MULTI_AGENT,
                max_turns=1000,
                auto_restart_on_early_termination=True,
                max_restart_attempts=3
            )
            
            # Initialize builder with project root
            builder = MultiAgentMemoryBankBuilder(root_path=project_root)
            
            # Build memory bank directly with config and progress callback
            build_result = await asyncio.wait_for(
                builder.build_memory_bank(build_config, progress_callback=progress_callback),
                timeout=timeout_minutes * 60
            )
            
            return {
                "success": build_result.success,
                "error": build_result.errors[0] if build_result.errors else None
            }
            
        except ImportError as e:
            logger.error(f"Memory bank builder not available: {e}")
            return {
                "success": False,
                "error": f"Memory bank builder not available: {e}. Please ensure memory_bank_core is properly installed."
            }
        except asyncio.TimeoutError:
            logger.error(f"Memory bank build timed out after {timeout_minutes} minutes")
            return {
                "success": False,
                "error": f"Memory bank build timed out after {timeout_minutes} minutes"
            }
        except Exception as e:
            logger.error(f"Memory bank build failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_directory_stats(self, directory: Path) -> tuple[int, int]:
        """Get statistics about a directory."""
        if not directory.exists():
            return 0, 0
        
        files_count = 0
        total_size = 0
        
        for item in directory.rglob("*"):
            if item.is_file():
                files_count += 1
                total_size += item.stat().st_size
        
        return files_count, total_size
    
    async def copy_memory_bank_to_sandbox(
        self,
        experiment_memory_bank: ExperimentMemoryBank,
        sandbox_path: Path
    ) -> bool:
        """Copy pre-built memory bank to a sandbox directory.
        
        Args:
            experiment_memory_bank: Pre-built experiment memory bank
            sandbox_path: Target sandbox directory
            
        Returns:
            True if copy successful, False otherwise
        """
        try:
            if not experiment_memory_bank.is_valid():
                logger.error(f"Experiment memory bank is invalid: {experiment_memory_bank.memory_bank_path}")
                return False
            
            target_memory_bank_path = sandbox_path / "memory-bank"
            
            # Remove existing memory bank if present
            if target_memory_bank_path.exists():
                shutil.rmtree(target_memory_bank_path)
            
            # Copy memory bank
            shutil.copytree(experiment_memory_bank.memory_bank_path, target_memory_bank_path)
            
            logger.info(f"Memory bank copied to sandbox: {target_memory_bank_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy memory bank to sandbox: {e}")
            return False
    
    async def get_memory_bank(self, experiment_id: str) -> Optional[ExperimentMemoryBank]:
        """Get existing memory bank for an experiment.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            ExperimentMemoryBank if found and valid, None otherwise
        """
        if experiment_id in self.active_memory_banks:
            memory_bank = self.active_memory_banks[experiment_id]
            if memory_bank.is_valid():
                return memory_bank
            else:
                # Remove invalid memory bank
                del self.active_memory_banks[experiment_id]
        
        return None
    
    async def cleanup_memory_bank(self, experiment_id: str) -> bool:
        """Clean up memory bank for an experiment.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if experiment_id in self.active_memory_banks:
                memory_bank = self.active_memory_banks[experiment_id]
                
                # Remove directory
                if memory_bank.memory_bank_path.exists():
                    shutil.rmtree(memory_bank.memory_bank_path.parent)  # Remove entire experiment dir
                    logger.info(f"Cleaned up memory bank directory for experiment {experiment_id}")
                
                # Remove from active memory banks
                del self.active_memory_banks[experiment_id]
                
                return True
            else:
                logger.warning(f"No memory bank found for experiment {experiment_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cleanup memory bank for experiment {experiment_id}: {e}")
            return False
    
    async def list_active_memory_banks(self) -> Dict[str, ExperimentMemoryBank]:
        """Get all active experiment memory banks.
        
        Returns:
            Dictionary of experiment_id -> ExperimentMemoryBank
        """
        # Filter out invalid memory banks
        valid_memory_banks = {}
        for exp_id, memory_bank in self.active_memory_banks.items():
            if memory_bank.is_valid():
                valid_memory_banks[exp_id] = memory_bank
            else:
                logger.warning(f"Removing invalid memory bank for experiment {exp_id}")
        
        # Update active memory banks
        self.active_memory_banks = valid_memory_banks
        
        return valid_memory_banks.copy()
    
    async def get_memory_bank_stats(self) -> Dict[str, Any]:
        """Get statistics about all experiment memory banks.
        
        Returns:
            Dictionary with memory bank statistics
        """
        active_memory_banks = await self.list_active_memory_banks()
        
        total_experiments = len(active_memory_banks)
        total_size = sum(mb.total_size_bytes for mb in active_memory_banks.values())
        total_files = sum(mb.files_count for mb in active_memory_banks.values())
        
        return {
            "total_experiments": total_experiments,
            "total_memory_banks": total_experiments,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_files": total_files,
            "avg_size_mb": (total_size / (1024 * 1024)) / total_experiments if total_experiments > 0 else 0,
            "base_directory": str(self.base_memory_bank_dir),
            "experiments": {
                exp_id: {
                    "files_count": mb.files_count,
                    "size_mb": mb.total_size_mb,
                    "build_time_seconds": mb.build_time_seconds,
                    "commit_hash": mb.repo_commit_hash,
                    "created_at": mb.created_at.isoformat()
                }
                for exp_id, mb in active_memory_banks.items()
            }
        }