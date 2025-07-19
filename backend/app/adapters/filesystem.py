import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.models.memory_bank import (
    MemoryBank, MemoryBankFile, Task, ChangelogEntry, 
    GenerationSummary, Graph, MemoryBankSummary
)

class FileSystemAdapter:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
    
    def get_memory_banks(self) -> List[MemoryBankSummary]:
        """Get all memory banks in the root directory"""
        memory_banks = []
        
        for item in self.root_path.iterdir():
            if item.is_dir() and "memory_bank" in item.name:
                memory_bank_path = item / "memory-bank"
                if memory_bank_path.exists():
                    summary = self._get_memory_bank_summary(item.name, str(item))
                    if summary:
                        memory_banks.append(summary)
        
        return memory_banks
    
    def get_memory_bank(self, name: str) -> Optional[MemoryBank]:
        """Get a specific memory bank by name"""
        memory_bank_dir = self.root_path / name
        if not memory_bank_dir.exists():
            return None
        
        memory_bank_path = memory_bank_dir / "memory-bank"
        if not memory_bank_path.exists():
            return None
        
        files = self._parse_memory_bank_files(memory_bank_path)
        tasks = self._parse_tasks(memory_bank_path / "tasks")
        changelog = self._parse_changelog(memory_bank_path / "changelog.md")
        generation_summary = self._parse_generation_summary(memory_bank_dir / "generation_summary.json")
        graph = self._parse_graph(memory_bank_dir / "graph.json")
        
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
    
    def _get_memory_bank_summary(self, name: str, path: str) -> Optional[MemoryBankSummary]:
        """Get summary information for a memory bank"""
        memory_bank_path = Path(path) / "memory-bank"
        if not memory_bank_path.exists():
            return None
        
        # Count files
        file_count = len([f for f in memory_bank_path.iterdir() if f.is_file() and f.suffix == ".md"])
        
        # Count tasks
        tasks_dir = memory_bank_path / "tasks"
        task_count = 0
        if tasks_dir.exists():
            task_count = len([f for f in tasks_dir.iterdir() if f.is_file() and f.suffix == ".md"])
        
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
    
    def _parse_memory_bank_files(self, memory_bank_path: Path) -> List[MemoryBankFile]:
        """Parse markdown files in the memory bank"""
        files = []
        
        for file_path in memory_bank_path.iterdir():
            if file_path.is_file() and file_path.suffix == ".md":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    stat = file_path.stat()
                    files.append(MemoryBankFile(
                        name=file_path.name,
                        path=str(file_path),
                        content=content,
                        last_modified=datetime.fromtimestamp(stat.st_mtime),
                        size=stat.st_size
                    ))
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
        
        return files
    
    def _parse_tasks(self, tasks_dir: Path) -> List[Task]:
        """Parse tasks from tasks directory"""
        tasks = []
        
        if not tasks_dir.exists():
            return tasks
        
        for task_file in tasks_dir.iterdir():
            if task_file.is_file() and task_file.suffix == ".md":
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse task metadata from the file content
                    task = self._parse_task_content(task_file.stem, content)
                    if task:
                        tasks.append(task)
                except Exception as e:
                    print(f"Error reading task file {task_file}: {e}")
        
        return tasks
    
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
    
    def _parse_changelog(self, changelog_path: Path) -> List[ChangelogEntry]:
        """Parse changelog from markdown file"""
        changelog_entries = []
        
        if not changelog_path.exists():
            return changelog_entries
        
        try:
            with open(changelog_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
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
            print(f"Error parsing changelog: {e}")
        
        return changelog_entries
    
    def _parse_generation_summary(self, summary_path: Path) -> Optional[GenerationSummary]:
        """Parse generation summary JSON file"""
        if not summary_path.exists():
            return None
        
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return GenerationSummary(
                generated_at=datetime.fromisoformat(data['generated_at'].replace('Z', '+00:00')),
                repo_path=data['repo_path'],
                files_written=data['files_written'],
                num_messages=data.get('num_messages', data.get('num_files', 0)),  # Handle both old and new formats
                method=data['method']
            )
        except Exception as e:
            print(f"Error parsing generation summary: {e}")
            return None
    
    def _parse_graph(self, graph_path: Path) -> Optional[Graph]:
        """Parse graph JSON file"""
        if not graph_path.exists():
            return None
        
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Graph(
                nodes=data.get('nodes', []),
                edges=data.get('edges', []),
                metadata=data.get('metadata', {})
            )
        except Exception as e:
            print(f"Error parsing graph: {e}")
            return None