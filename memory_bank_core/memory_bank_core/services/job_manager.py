"""
Job Manager for memory bank building operations
Extracted from backend to be reusable standalone
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

from ..models.build_job import (
    BuildJob, 
    BuildJobStatus, 
    BuildJobType,
    BuildJobRequest,
    BuildConfig,
    BuildMode
)
from ..interfaces.storage import JobStorageInterface
from ..interfaces.validation import JobValidationInterface, DefaultJobValidator
# Optional import for CoreMemoryBankBuilder
try:
    from ..builders.core_builder import CoreMemoryBankBuilder
except ImportError:
    CoreMemoryBankBuilder = None
from ..integrations.legacy import LegacyScriptExecutor

logger = logging.getLogger(__name__)


class JobManager:
    """Manages build jobs for memory bank creation and updates"""
    
    def __init__(
        self, 
        root_path: str,
        job_storage: Optional[JobStorageInterface] = None,
        job_validator: Optional[JobValidationInterface] = None,
        memory_bank_builder: Optional[CoreMemoryBankBuilder] = None,
        legacy_executor: Optional[LegacyScriptExecutor] = None,
        max_concurrent_jobs: int = 3
    ):
        """
        Initialize the job manager
        
        Args:
            root_path: Root path for memory banks
            job_storage: Storage adapter for job logs and metadata
            job_validator: Validator for job requests
            memory_bank_builder: Memory bank builder instance
            legacy_executor: Legacy script executor for backward compatibility
            max_concurrent_jobs: Maximum number of concurrent jobs
        """
        self.root_path = Path(root_path)
        self.jobs: Dict[str, BuildJob] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
        self.max_concurrent_jobs = max_concurrent_jobs
        
        # Set up storage adapter
        if job_storage is None:
            job_storage = DefaultJobStorageAdapter(self.root_path)
        self.job_storage = job_storage
        
        # Set up validator
        if job_validator is None:
            job_validator = DefaultJobValidator(
                root_path=str(self.root_path),
                get_running_jobs_count_func=lambda: len(self.get_jobs_by_status(BuildJobStatus.RUNNING))
            )
        self.job_validator = job_validator
        
        # Set up memory bank builder
        if memory_bank_builder is None:
            if CoreMemoryBankBuilder is not None:
                memory_bank_builder = CoreMemoryBankBuilder(self.root_path)
            else:
                memory_bank_builder = None
        self.memory_bank_builder = memory_bank_builder
        
        # Set up legacy executor
        if legacy_executor is None:
            legacy_executor = LegacyScriptExecutor(self.root_path)
        self.legacy_executor = legacy_executor
    
    async def start_worker(self):
        """Start the background worker to process jobs"""
        if self.worker_task and not self.worker_task.done():
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
    
    async def stop_worker(self):
        """Stop the background worker"""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
    
    async def _worker_loop(self):
        """Background worker loop to process jobs"""
        while self.running:
            try:
                job_id = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                await self._process_job(job_id)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
    
    async def create_job(self, request: BuildJobRequest) -> BuildJob:
        """Create a new build job"""
        # Validate request
        await self.job_validator.validate_build_request(request)
        
        job_id = str(uuid.uuid4())
        
        # Generate output path if not provided
        if request.output_name:
            output_path = str(self.root_path / request.output_name)
        else:
            repo_name = Path(request.repo_path).name
            output_path = str(self.root_path / f"{repo_name}_memory_bank")
        
        job = BuildJob(
            id=job_id,
            type=request.type,
            status=BuildJobStatus.PENDING,
            repo_path=request.repo_path,
            memory_bank_name=request.memory_bank_name,
            output_path=output_path,
            created_at=datetime.now(),
            logs=[]
        )
        
        self.jobs[job_id] = job
        await self.job_queue.put(job_id)
        
        return job
    
    async def _process_job(self, job_id: str):
        """Process a single job"""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found")
            return
        
        job = self.jobs[job_id]
        
        try:
            # Check if job was cancelled
            if job.status == BuildJobStatus.CANCELLED:
                job.logs.append("Job was cancelled")
                return
            
            # Update job status
            job.status = BuildJobStatus.RUNNING
            job.started_at = datetime.now()
            job.logs.append(f"Started job {job_id} at {job.started_at}")
            
            # Execute the appropriate build operation
            if job.type == BuildJobType.BUILD:
                await self._execute_build_command(job)
            elif job.type == BuildJobType.UPDATE:
                await self._execute_update_command(job)
            else:
                raise ValueError(f"Unknown job type: {job.type}")
            
            # Mark as completed
            job.status = BuildJobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.logs.append(f"Job completed successfully at {job.completed_at}")
            
        except Exception as e:
            job.status = BuildJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            job.logs.append(f"ERROR: {str(e)}")
            logger.error(f"Job {job_id} failed: {e}")
        finally:
            # Always save logs at the end of job processing
            await self.job_storage.save_job_logs(job)
    
    async def _execute_build_command(self, job: BuildJob):
        """Execute the build memory bank command"""
        try:
            # Create progress callback to update job logs
            log_save_counter = [0]  # Use list to modify in closure
            
            async def progress_callback(message: str):
                job.logs.append(message)
                logger.info(f"Build progress: {message}")
                
                # Write to stdout immediately with explicit flushing for streaming capture
                import sys
                sys.stdout.write(f"[BUILD_PROGRESS] {message}\n")
                sys.stdout.flush()
                
                # Also write to stderr as backup for streaming systems that monitor both
                sys.stderr.write(f"[BUILD_PROGRESS] {message}\n")
                sys.stderr.flush()
                
                # Save logs periodically (every 10 log entries)
                log_save_counter[0] += 1
                if log_save_counter[0] % 10 == 0:
                    await self.job_storage.save_job_logs(job)
            
            # Check if legacy mode is enabled
            if self.legacy_executor.is_enabled():
                output_name = Path(job.output_path).name
                result = await self.legacy_executor.execute_legacy_build(
                    repo_path=job.repo_path,
                    output_name=output_name,
                    progress_callback=progress_callback
                )
            else:
                # Check if memory bank builder is available
                if self.memory_bank_builder is None:
                    raise RuntimeError("Memory bank builder not available. Either enable legacy mode or install claude_code_sdk.")
                
                # Create build configuration
                system_prompt_path = str(self.root_path / "prompts" / "system_prompt.md")
                
                # Check if system prompt exists and print warning if not found
                if not Path(system_prompt_path).exists():
                    print(f"WARNING: system_prompt.md not found at {system_prompt_path}")
                    logger.warning(f"system_prompt.md not found at {system_prompt_path}")
                
                config = BuildConfig(
                    repo_path=job.repo_path,
                    output_path=job.output_path,
                    mode=BuildMode.FULL,
                    system_prompt_path=system_prompt_path,
                    max_turns=1000,  # Reasonable limit for memory bank generation
                    auto_restart_on_early_termination=False,  # Temporarily disable to test
                    max_restart_attempts=1  # Reduce to 1 for testing
                )
                
                # Use the memory bank builder
                build_result = await self.memory_bank_builder.build_memory_bank(
                    config=config,
                    progress_callback=progress_callback
                )
                
                # Convert BuildResult to dict for compatibility
                result = {
                    "success": build_result.success,
                    "output_path": build_result.output_path,
                    "files_written": build_result.files_written,
                    "metadata": build_result.metadata,
                    "errors": build_result.errors
                }
            
            # Store result in job
            job.result = result
            job.logs.append(f"Memory bank built successfully at: {result['output_path']}")
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            raise
    
    async def _execute_update_command(self, job: BuildJob):
        """Execute the update memory bank command"""
        if not job.memory_bank_name:
            raise ValueError("Memory bank name is required for update operations")
        
        try:
            # Create progress callback to update job logs
            log_save_counter = [0]  # Use list to modify in closure
            
            async def progress_callback(message: str):
                job.logs.append(message)
                logger.info(f"Update progress: {message}")
                
                # Write to stdout immediately with explicit flushing for streaming capture
                import sys
                sys.stdout.write(f"[UPDATE_PROGRESS] {message}\n")
                sys.stdout.flush()
                
                # Also write to stderr as backup for streaming systems that monitor both
                sys.stderr.write(f"[UPDATE_PROGRESS] {message}\n")
                sys.stderr.flush()
                
                # Save logs periodically (every 10 log entries)
                log_save_counter[0] += 1
                if log_save_counter[0] % 10 == 0:
                    await self.job_storage.save_job_logs(job)
            
            # Check if legacy mode is enabled
            if self.legacy_executor.is_enabled():
                result = await self.legacy_executor.execute_legacy_update(
                    repo_path=job.repo_path,
                    memory_bank_name=job.memory_bank_name,
                    progress_callback=progress_callback
                )
            else:
                # Check if memory bank builder is available
                if self.memory_bank_builder is None:
                    raise RuntimeError("Memory bank builder not available. Either enable legacy mode or install claude_code_sdk.")
                
                # Create build configuration for incremental update
                output_path = self.root_path / job.memory_bank_name
                system_prompt_path = str(self.root_path / "prompts" / "system_prompt.md")
                
                # Check if system prompt exists and print warning if not found
                if not Path(system_prompt_path).exists():
                    print(f"WARNING: system_prompt.md not found at {system_prompt_path}")
                    logger.warning(f"system_prompt.md not found at {system_prompt_path}")
                
                config = BuildConfig(
                    repo_path=job.repo_path,
                    output_path=str(output_path),
                    mode=BuildMode.INCREMENTAL,
                    system_prompt_path=system_prompt_path,
                    max_turns=5000,
                    auto_restart_on_early_termination=False,  # Temporarily disable to test
                    max_restart_attempts=1  # Reduce to 1 for testing
                )
                
                # Use the memory bank builder for updates
                build_result = await self.memory_bank_builder.build_memory_bank(
                    config=config,
                    progress_callback=progress_callback
                )
                
                # Convert BuildResult to dict for compatibility
                result = {
                    "success": build_result.success,
                    "output_path": build_result.output_path,
                    "files_written": build_result.files_written,
                    "metadata": build_result.metadata,
                    "errors": build_result.errors
                }
            
            # Store result in job
            job.result = result
            job.logs.append(f"Memory bank updated successfully: {job.memory_bank_name}")
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise
    
    def get_job(self, job_id: str) -> Optional[BuildJob]:
        """Get a job by ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[BuildJob]:
        """Get all jobs"""
        return list(self.jobs.values())
    
    def get_jobs_by_status(self, status: BuildJobStatus) -> List[BuildJob]:
        """Get jobs by status"""
        return [job for job in self.jobs.values() if job.status == status]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job (only if it's pending)"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        if job.status == BuildJobStatus.PENDING:
            job.status = BuildJobStatus.CANCELLED
            job.completed_at = datetime.now()
            return True
        
        return False


class DefaultJobStorageAdapter(JobStorageInterface):
    """Default filesystem-based job storage adapter"""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
    
    async def get_log_file_path(self, job: BuildJob) -> Path:
        """Generate a log file path with session identifier"""
        # Create logs directory in the memory bank folder
        if job.type == BuildJobType.BUILD:
            logs_dir = Path(job.output_path) / "logs"
        else:  # UPDATE
            logs_dir = self.root_path / job.memory_bank_name / "logs"
        
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp and job ID
        timestamp = job.created_at.strftime("%Y%m%d_%H%M%S")
        log_filename = f"build_job_{timestamp}_{job.id[:8]}.log"
        
        return logs_dir / log_filename
    
    async def save_job_logs(self, job: BuildJob) -> None:
        """Save job logs to a file"""
        try:
            log_file_path = await self.get_log_file_path(job)
            
            # Extract system prompt and full prompt from logs if available
            system_prompt = None
            full_prompt = None
            for log in job.logs:
                if log.startswith("[SYSTEM_PROMPT_CONTENT]"):
                    system_prompt = log.replace("[SYSTEM_PROMPT_CONTENT]", "").strip()
                elif log.startswith("[FULL_PROMPT]"):
                    full_prompt = log.replace("[FULL_PROMPT]", "").strip()
            
            # Create log data with metadata
            log_data = {
                "job_id": job.id,
                "type": job.type.value,
                "status": job.status.value,
                "repo_path": job.repo_path,
                "memory_bank_name": job.memory_bank_name,
                "output_path": job.output_path,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "system_prompt": system_prompt,
                "full_prompt": full_prompt,
                "logs": job.logs,
                "result": job.result
            }
            
            # Write logs in both JSON and readable format
            # JSON format for programmatic access
            json_file_path = log_file_path.with_suffix('.json')
            with open(json_file_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            # Human-readable format
            with open(log_file_path, 'w') as f:
                f.write(f"Build Job Log\n")
                f.write(f"=" * 80 + "\n")
                f.write(f"Job ID: {job.id}\n")
                f.write(f"Type: {job.type.value}\n")
                f.write(f"Status: {job.status.value}\n")
                f.write(f"Repository: {job.repo_path}\n")
                f.write(f"Memory Bank: {job.memory_bank_name or 'N/A'}\n")
                f.write(f"Output Path: {job.output_path}\n")
                f.write(f"Created: {job.created_at}\n")
                f.write(f"Started: {job.started_at or 'N/A'}\n")
                f.write(f"Completed: {job.completed_at or 'N/A'}\n")
                if job.error_message:
                    f.write(f"Error: {job.error_message}\n")
                f.write(f"=" * 80 + "\n\n")
                
                # Write system prompt if available
                if system_prompt:
                    f.write("System Prompt:\n")
                    f.write("-" * 80 + "\n")
                    f.write(system_prompt + "\n")
                    f.write("-" * 80 + "\n\n")
                
                # Write full prompt if available
                if full_prompt:
                    f.write("Full Prompt (Task Instructions):\n")
                    f.write("-" * 80 + "\n")
                    f.write(full_prompt + "\n")
                    f.write("-" * 80 + "\n\n")
                
                # Write logs with timestamps
                f.write("Log Entries:\n")
                f.write("-" * 80 + "\n")
                for i, log_entry in enumerate(job.logs, 1):
                    f.write(f"[{i:04d}] {log_entry}\n")
                
                # Write result if available
                if job.result:
                    f.write("\n" + "=" * 80 + "\n")
                    f.write("Job Result:\n")
                    f.write("-" * 80 + "\n")
                    f.write(json.dumps(job.result, indent=2))
            
            logger.info(f"Saved job logs to: {log_file_path}")
            job.logs.append(f"Logs saved to: {log_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save job logs: {e}")
            job.logs.append(f"Failed to save logs to file: {e}")
    
    async def load_job_logs(self, job_id: str) -> Optional[Dict]:
        """Load job logs from storage (not implemented in basic version)"""
        # This could be implemented to search for log files by job ID
        # For now, return None to indicate not implemented
        return None
    
    async def cleanup_old_logs(self, max_age_days: int = 30) -> int:
        """Clean up old log files (not implemented in basic version)"""
        # This could be implemented to clean up old log files
        # For now, return 0 to indicate no cleanup performed
        return 0
