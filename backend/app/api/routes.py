from fastapi import APIRouter, HTTPException
from typing import List
from app.services.memory_bank_service import MemoryBankService
from app.models.memory_bank import MemoryBank, MemoryBankSummary

# Initialize the service with the current directory
# This will be configurable later
import os
ROOT_PATH = os.path.join(os.path.dirname(__file__), "../../../")
memory_bank_service = MemoryBankService(ROOT_PATH)

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