import asyncio
import subprocess
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import logging
import json

from app.models.memory_bank import (
    BuildJob, 
    BuildJobStatus, 
    BuildJobType,
    BuildJobRequest
)
from app.services.memory_bank_builder import MemoryBankBuilder
from app.services.backward_compat import BackwardCompatibilityMode

logger = logging.getLogger(__name__)


class BuildJobService:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.jobs: Dict[str, BuildJob] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
        self.memory_bank_builder = MemoryBankBuilder(self.root_path)
    
    def _get_log_file_path(self, job: BuildJob) -> Path:
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
    
    def _save_job_logs(self, job: BuildJob):
        """Save job logs to a file"""
        try:
            log_file_path = self._get_log_file_path(job)
            
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
                print(f"Error in worker loop: {e}")
    
    async def create_job(self, request: BuildJobRequest) -> BuildJob:
        """Create a new build job"""
        # Validate request
        await self._validate_build_request(request)
        
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
    
    async def _validate_build_request(self, request: BuildJobRequest):
        """Validate a build request"""
        # Check if repository path exists
        if not os.path.exists(request.repo_path):
            raise ValueError(f"Repository path does not exist: {request.repo_path}")
        
        # For update operations, check if memory bank exists
        if request.type == BuildJobType.UPDATE:
            if not request.memory_bank_name:
                raise ValueError("Memory bank name is required for update operations")
            
            memory_bank_path = self.root_path / request.memory_bank_name
            if not memory_bank_path.exists():
                raise ValueError(f"Memory bank does not exist: {request.memory_bank_name}")
        
        # Check if there are too many running jobs
        running_jobs = len(self.get_jobs_by_status(BuildJobStatus.RUNNING))
        if running_jobs >= 3:  # Limit concurrent jobs
            raise ValueError("Too many jobs are currently running. Please wait for some to complete.")
    
    async def _process_job(self, job_id: str):
        """Process a single job"""
        if job_id not in self.jobs:
            print(f"Job {job_id} not found")
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
            
            # Execute the appropriate CLI command
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
            print(f"Job {job_id} failed: {e}")
        finally:
            # Always save logs at the end of job processing
            self._save_job_logs(job)
    
    async def _execute_build_command(self, job: BuildJob):
        """Execute the build memory bank command using integrated builder"""
        try:
            # Check if backward compatibility mode is enabled
            if BackwardCompatibilityMode.is_enabled():
                job.logs.append("Using legacy bash script mode (USE_LEGACY_SCRIPTS=true)")
                result = await BackwardCompatibilityMode.execute_legacy_build(
                    root_path=self.root_path,
                    repo_path=job.repo_path,
                    output_name=Path(job.output_path).name,
                    logs=job.logs
                )
            else:
                # Create progress callback to update job logs
                log_save_counter = [0]  # Use list to modify in closure
                
                async def progress_callback(message: str):
                    job.logs.append(message)
                    logger.info(f"Build progress: {message}")
                    
                    # Save logs periodically (every 10 log entries)
                    log_save_counter[0] += 1
                    if log_save_counter[0] % 10 == 0:
                        self._save_job_logs(job)
                
                # Use the integrated memory bank builder
                result = await self.memory_bank_builder.build_memory_bank(
                    repo_path=job.repo_path,
                    output_name=Path(job.output_path).name,
                    progress_callback=progress_callback
                )
            
            # Store result in job
            job.result = result
            job.logs.append(f"Memory bank built successfully at: {result.get('output_path', job.output_path)}")
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            raise
    
    async def _execute_update_command(self, job: BuildJob):
        """Execute the update memory bank command using integrated builder"""
        if not job.memory_bank_name:
            raise ValueError("Memory bank name is required for update operations")
        
        try:
            # Check if backward compatibility mode is enabled
            if BackwardCompatibilityMode.is_enabled():
                job.logs.append("Using legacy bash script mode (USE_LEGACY_SCRIPTS=true)")
                result = await BackwardCompatibilityMode.execute_legacy_update(
                    root_path=self.root_path,
                    repo_path=job.repo_path,
                    memory_bank_name=job.memory_bank_name,
                    logs=job.logs
                )
            else:
                # Create progress callback to update job logs
                log_save_counter = [0]  # Use list to modify in closure
                
                async def progress_callback(message: str):
                    job.logs.append(message)
                    logger.info(f"Update progress: {message}")
                    
                    # Save logs periodically (every 10 log entries)
                    log_save_counter[0] += 1
                    if log_save_counter[0] % 10 == 0:
                        self._save_job_logs(job)
                
                # Use the integrated memory bank builder for updates
                result = await self.memory_bank_builder.update_memory_bank(
                    repo_path=job.repo_path,
                    memory_bank_name=job.memory_bank_name,
                    progress_callback=progress_callback
                )
            
            # Store result in job
            job.result = result
            job.logs.append(f"Memory bank updated successfully: {job.memory_bank_name}")
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise
    
    # The _run_command method has been removed as we now use direct Python integration
    # instead of subprocess calls to bash scripts
    
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