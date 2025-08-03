from typing import Dict, List, Optional
from pathlib import Path
import logging

from app.models.memory_bank import (
    BuildJob, 
    BuildJobStatus, 
    BuildJobType,
    BuildJobRequest
)
from core.services import JobManager
from core.integrations.legacy import LegacyScriptExecutor

logger = logging.getLogger(__name__)


class BuildJobService:
    """Backend adapter for core JobManager - maintains existing API surface"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        # Use the core JobManager with legacy support
        self.core_job_manager = JobManager(
            root_path=str(self.root_path),
            legacy_executor=LegacyScriptExecutor(self.root_path)
        )
    
    # Delegate all operations to the core JobManager
    async def start_worker(self):
        """Start the background worker to process jobs"""
        await self.core_job_manager.start_worker()
    
    async def stop_worker(self):
        """Stop the background worker"""
        await self.core_job_manager.stop_worker()
    
    async def create_job(self, request: BuildJobRequest) -> BuildJob:
        """Create a new build job"""
        return await self.core_job_manager.create_job(request)
    
    def get_job(self, job_id: str) -> Optional[BuildJob]:
        """Get a job by ID"""
        return self.core_job_manager.get_job(job_id)
    
    def get_all_jobs(self) -> List[BuildJob]:
        """Get all jobs"""
        return self.core_job_manager.get_all_jobs()
    
    def get_jobs_by_status(self, status: BuildJobStatus) -> List[BuildJob]:
        """Get jobs by status"""
        return self.core_job_manager.get_jobs_by_status(status)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job (only if it's pending)"""
        return self.core_job_manager.cancel_job(job_id)
    
    # Legacy methods for backward compatibility (deprecated but kept for existing code)
    def _save_job_logs(self, job: BuildJob):
        """DEPRECATED: Log saving is now handled by core JobManager"""
        logger.warning("_save_job_logs is deprecated - logs are now handled by core JobManager")
    
    def _get_log_file_path(self, job: BuildJob) -> Path:
        """DEPRECATED: Log file paths are now handled by core JobManager"""
        logger.warning("_get_log_file_path is deprecated - use core JobManager instead")
        return Path("deprecated")