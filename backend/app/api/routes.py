from fastapi import APIRouter, HTTPException
from typing import List
from app.services.memory_bank_service import MemoryBankService
from app.services.build_job_service import BuildJobService
from app.models.memory_bank import (
    MemoryBank, 
    MemoryBankSummary,
    BuildJob,
    BuildJobRequest,
    BuildJobResponse,
    BuildJobStatus
)

# Initialize the services with the current directory
# This will be configurable later
import os
ROOT_PATH = os.path.join(os.path.dirname(__file__), "../../../")
memory_bank_service = MemoryBankService(ROOT_PATH)
build_job_service = BuildJobService(ROOT_PATH)

router = APIRouter()

@router.get("/memory-banks", response_model=List[MemoryBankSummary])
async def get_memory_banks():
    """Get all memory banks"""
    return memory_bank_service.get_all_memory_banks()

@router.get("/memory-banks/{name}", response_model=MemoryBank)
async def get_memory_bank(name: str):
    """Get detailed information for a specific memory bank"""
    memory_bank = memory_bank_service.get_memory_bank(name)
    if not memory_bank:
        raise HTTPException(status_code=404, detail="Memory bank not found")
    return memory_bank

@router.get("/memory-banks/{name}/files")
async def get_memory_bank_files(name: str):
    """Get list of files in a memory bank"""
    files = memory_bank_service.get_memory_bank_files(name)
    return {"files": files}

@router.get("/memory-banks/{name}/files/{filename}")
async def get_memory_bank_file_content(name: str, filename: str):
    """Get content of a specific file in a memory bank"""
    content = memory_bank_service.get_memory_bank_file_content(name, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"filename": filename, "content": content}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Build job endpoints
@router.post("/builds", response_model=BuildJobResponse)
async def create_build_job(request: BuildJobRequest):
    """Create a new build job"""
    try:
        job = await build_job_service.create_job(request)
        return BuildJobResponse(
            id=job.id,
            status=job.status,
            created_at=job.created_at,
            message=f"Build job created for {request.repo_path}"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/builds", response_model=List[BuildJob])
async def get_all_build_jobs():
    """Get all build jobs"""
    return build_job_service.get_all_jobs()

@router.get("/builds/{job_id}", response_model=BuildJob)
async def get_build_job(job_id: str):
    """Get a specific build job"""
    job = build_job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Build job not found")
    return job

@router.get("/builds/{job_id}/status")
async def get_build_job_status(job_id: str):
    """Get build job status"""
    job = build_job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Build job not found")
    return {
        "id": job.id,
        "status": job.status,
        "progress": {
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "logs": job.logs[-10:] if job.logs else []  # Last 10 log lines
        }
    }

@router.post("/builds/{job_id}/cancel")
async def cancel_build_job(job_id: str):
    """Cancel a build job"""
    success = build_job_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel job")
    return {"message": "Job cancelled successfully"}