import asyncio
import subprocess
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from app.models.memory_bank import (
    BuildJob, 
    BuildJobStatus, 
    BuildJobType,
    BuildJobRequest
)


class BuildJobService:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.jobs: Dict[str, BuildJob] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
    
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
    
    async def _execute_build_command(self, job: BuildJob):
        """Execute the build memory bank command"""
        build_script = self.root_path / "build_memory_bank.sh"
        
        if not build_script.exists():
            raise FileNotFoundError("build_memory_bank.sh not found")
        
        # Prepare command
        cmd = [
            "bash",
            str(build_script),
            job.repo_path,
            Path(job.output_path).name  # Just the output name, not full path
        ]
        
        await self._run_command(job, cmd)
    
    async def _execute_update_command(self, job: BuildJob):
        """Execute the update memory bank command"""
        update_script = self.root_path / "update_memory_bank.sh"
        
        if not update_script.exists():
            raise FileNotFoundError("update_memory_bank.sh not found")
        
        if not job.memory_bank_name:
            raise ValueError("Memory bank name is required for update operations")
        
        # Prepare command
        cmd = [
            "bash",
            str(update_script),
            job.repo_path,
            job.memory_bank_name
        ]
        
        await self._run_command(job, cmd)
    
    async def _run_command(self, job: BuildJob, cmd: List[str]):
        """Run a command and capture output"""
        job.logs.append(f"Executing: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(self.root_path)
        )
        
        # Read output line by line
        async for line in process.stdout:
            decoded_line = line.decode('utf-8').strip()
            if decoded_line:
                job.logs.append(decoded_line)
        
        # Wait for process to complete
        return_code = await process.wait()
        
        if return_code != 0:
            raise subprocess.CalledProcessError(
                return_code, 
                cmd, 
                f"Command failed with return code {return_code}"
            )
        
        job.logs.append("Command completed successfully")
    
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