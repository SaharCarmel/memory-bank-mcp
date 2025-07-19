"""
File system operations implementation
"""

import json
import re
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..interfaces.filesystem import FileSystemOperations
from ..models.memory_bank import MemoryBankFile, Task, ChangelogEntry, GenerationSummary, Graph
from ..exceptions.storage import FileSystemError


class FileSystemOperationsImpl(FileSystemOperations):
    """Implementation of file system operations"""
    
    async def read_file(self, file_path: Path) -> str:
        """Read content from a file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            raise FileSystemError(f"Failed to read file {file_path}", str(e))
    
    async def write_file(self, file_path: Path, content: str) -> None:
        """Write content to a file"""
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
        except Exception as e:
            raise FileSystemError(f"Failed to write file {file_path}", str(e))
    
    async def create_directory(self, dir_path: Path) -> None:
        """Create a directory and its parents if they don't exist"""
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileSystemError(f"Failed to create directory {dir_path}", str(e))
    
    async def list_files(self, dir_path: Path, pattern: str = "*") -> List[Path]:
        """List files in a directory matching a pattern"""
        try:
            if not dir_path.exists():
                return []
            return list(dir_path.glob(pattern))
        except Exception as e:
            raise FileSystemError(f"Failed to list files in {dir_path}", str(e))
    
    async def parse_memory_bank_files(self, memory_bank_path: Path) -> List[MemoryBankFile]:
        """Parse memory bank files from a directory"""
        files = []
        
        try:
            for file_path in memory_bank_path.iterdir():
                if file_path.is_file() and file_path.suffix == ".md":
                    content = await self.read_file(file_path)
                    stat = file_path.stat()
                    
                    files.append(MemoryBankFile(
                        name=file_path.name,
                        path=str(file_path),
                        content=content,
                        last_modified=datetime.fromtimestamp(stat.st_mtime),
                        size=stat.st_size
                    ))
        except Exception as e:
            raise FileSystemError(f"Failed to parse memory bank files from {memory_bank_path}", str(e))
        
        return files
    
    async def parse_tasks(self, tasks_dir: Path) -> List[Task]:
        """Parse tasks from a tasks directory"""
        tasks = []
        
        if not tasks_dir.exists():
            return tasks
        
        try:
            for task_file in tasks_dir.iterdir():
                if task_file.is_file() and task_file.suffix == ".md":
                    content = await self.read_file(task_file)
                    task = self._parse_task_content(task_file.stem, content)
                    if task:
                        tasks.append(task)
        except Exception as e:
            raise FileSystemError(f"Failed to parse tasks from {tasks_dir}", str(e))
        
        return tasks
    
    async def parse_changelog(self, changelog_path: Path) -> List[ChangelogEntry]:
        """Parse changelog from a markdown file"""
        changelog_entries = []
        
        if not changelog_path.exists():
            return changelog_entries
        
        try:
            content = await self.read_file(changelog_path)
            
            # Split by date headers (## [date])
            entries = re.split(r'\n## \[([^\]]+)\]', content)
            
            for i in range(1, len(entries), 2):
                if i + 1 < len(entries):
                    date = entries[i].strip()
                    entry_content = entries[i + 1].strip()
                    
                    # Parse the entry content
                    changes = []
                    files_changed = []
                    impact = None
                    
                    # Extract changes from bullet points
                    for line in entry_content.split('\n'):
                        if line.strip().startswith('- '):
                            changes.append(line.strip()[2:])
                        elif '**' in line and '**:' in line:
                            files_changed.append(line.strip())
                    
                    changelog_entries.append(ChangelogEntry(
                        date=date,
                        title=f"Changes for {date}",
                        changes=changes,
                        files_changed=files_changed,
                        impact=impact
                    ))
        except Exception as e:
            raise FileSystemError(f"Failed to parse changelog from {changelog_path}", str(e))
        
        return changelog_entries
    
    async def parse_generation_summary(self, summary_path: Path) -> Optional[GenerationSummary]:
        """Parse generation summary from JSON file"""
        if not summary_path.exists():
            return None
        
        try:
            content = await self.read_file(summary_path)
            data = json.loads(content)
            
            return GenerationSummary(
                generated_at=datetime.fromisoformat(data['generated_at'].replace('Z', '+00:00')),
                repo_path=data['repo_path'],
                files_written=data['files_written'],
                num_messages=data.get('num_messages', data.get('num_files', 0)),
                method=data['method']
            )
        except Exception as e:
            raise FileSystemError(f"Failed to parse generation summary from {summary_path}", str(e))
    
    async def parse_graph(self, graph_path: Path) -> Optional[Graph]:
        """Parse graph from JSON file"""
        if not graph_path.exists():
            return None
        
        try:
            content = await self.read_file(graph_path)
            data = json.loads(content)
            
            return Graph(
                nodes=data.get('nodes', []),
                edges=data.get('edges', []),
                metadata=data.get('metadata', {})
            )
        except Exception as e:
            raise FileSystemError(f"Failed to parse graph from {graph_path}", str(e))
    
    async def write_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write data to a JSON file"""
        try:
            content = json.dumps(data, indent=2, default=str)
            await self.write_file(file_path, content)
        except Exception as e:
            raise FileSystemError(f"Failed to write JSON to {file_path}", str(e))
    
    def _parse_task_content(self, task_id: str, content: str) -> Optional[Task]:
        """Parse individual task content"""
        lines = content.strip().split('\n')
        if not lines:
            return None
        
        # Extract title (first line, remove # if present)
        title = lines[0].strip()
        if title.startswith('#'):
            title = title[1:].strip()
        
        # Extract description (remaining content)
        description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else None
        
        return Task(
            id=task_id,
            title=title,
            description=description,
            status="unknown",  # Default status
            priority="medium"  # Default priority
        )