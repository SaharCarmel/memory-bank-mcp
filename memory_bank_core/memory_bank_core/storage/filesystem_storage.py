"""
File system storage implementation for memory banks
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..interfaces.storage import MemoryBankStorage
from ..interfaces.filesystem import FileSystemOperations
from ..models.memory_bank import MemoryBank, MemoryBankSummary
from ..exceptions.storage import MemoryBankNotFoundError, StorageAccessError


class FileSystemStorage(MemoryBankStorage):
    """File system implementation of memory bank storage"""
    
    def __init__(self, root_path: str, fs_ops: FileSystemOperations):
        self.root_path = Path(root_path)
        self.fs_ops = fs_ops
    
    async def get_memory_banks(self) -> List[MemoryBankSummary]:
        """Get all available memory banks"""
        memory_banks = []
        
        try:
            if not self.root_path.exists():
                return memory_banks
            
            for item in self.root_path.iterdir():
                if item.is_dir() and "memory_bank" in item.name:
                    memory_bank_path = item / "memory-bank"
                    if memory_bank_path.exists():
                        summary = await self._get_memory_bank_summary(item.name, str(item))
                        if summary:
                            memory_banks.append(summary)
        except Exception as e:
            raise StorageAccessError(f"Failed to list memory banks", str(e))
        
        return memory_banks
    
    async def get_memory_bank(self, name: str) -> Optional[MemoryBank]:
        """Get a specific memory bank by name"""
        memory_bank_dir = self.root_path / name
        if not memory_bank_dir.exists():
            return None
        
        memory_bank_path = memory_bank_dir / "memory-bank"
        if not memory_bank_path.exists():
            return None
        
        try:
            files = await self.fs_ops.parse_memory_bank_files(memory_bank_path)
            tasks = await self.fs_ops.parse_tasks(memory_bank_path / "tasks")
            changelog = await self.fs_ops.parse_changelog(memory_bank_path / "changelog.md")
            generation_summary = await self.fs_ops.parse_generation_summary(memory_bank_dir / "generation_summary.json")
            graph = await self.fs_ops.parse_graph(memory_bank_dir / "graph.json")
            
            return MemoryBank(
                name=name,
                path=str(memory_bank_dir),
                files=files,
                tasks=tasks,
                changelog=changelog,
                generation_summary=generation_summary,
                graph=graph,
                created_at=datetime.fromtimestamp(memory_bank_dir.stat().st_ctime),
                updated_at=datetime.fromtimestamp(memory_bank_dir.stat().st_mtime)
            )
        except Exception as e:
            raise StorageAccessError(f"Failed to load memory bank {name}", str(e))
    
    async def exists(self, name: str) -> bool:
        """Check if a memory bank exists"""
        memory_bank_dir = self.root_path / name
        memory_bank_path = memory_bank_dir / "memory-bank"
        return memory_bank_dir.exists() and memory_bank_path.exists()
    
    async def delete_memory_bank(self, name: str) -> bool:
        """Delete a memory bank"""
        memory_bank_dir = self.root_path / name
        if not memory_bank_dir.exists():
            return False
        
        try:
            import shutil
            shutil.rmtree(memory_bank_dir)
            return True
        except Exception as e:
            raise StorageAccessError(f"Failed to delete memory bank {name}", str(e))
    
    async def get_memory_bank_path(self, name: str) -> Optional[str]:
        """Get the filesystem path for a memory bank"""
        memory_bank_dir = self.root_path / name
        if await self.exists(name):
            return str(memory_bank_dir)
        return None
    
    async def _get_memory_bank_summary(self, name: str, path: str) -> Optional[MemoryBankSummary]:
        """Get summary information for a memory bank"""
        memory_bank_path = Path(path) / "memory-bank"
        if not memory_bank_path.exists():
            return None
        
        try:
            # Count files
            files = await self.fs_ops.list_files(memory_bank_path, "*.md")
            file_count = len(files)
            
            # Count tasks
            tasks_dir = memory_bank_path / "tasks"
            task_files = await self.fs_ops.list_files(tasks_dir, "*.md")
            task_count = len(task_files)
            
            # Check for changelog
            has_changelog = (memory_bank_path / "changelog.md").exists()
            
            return MemoryBankSummary(
                name=name,
                path=path,
                file_count=file_count,
                task_count=task_count,
                last_updated=datetime.fromtimestamp(memory_bank_path.stat().st_mtime),
                has_changelog=has_changelog
            )
        except Exception as e:
            raise StorageAccessError(f"Failed to get summary for memory bank {name}", str(e))