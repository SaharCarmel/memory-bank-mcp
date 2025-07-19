"""
Core Memory Bank Builder
Extracted from backend to be reusable standalone
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions, Message

from ..models.build_job import BuildConfig, BuildResult, BuildMode

logger = logging.getLogger(__name__)


class CoreMemoryBankBuilder:
    """Builds memory banks using Claude Code SDK"""
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.system_prompt_path = self.root_path / "system_prompt.md"
        
    async def _call_progress_callback(self, progress_callback: Optional[Callable], message: str):
        """Helper to handle both sync and async progress callbacks"""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(message)
            else:
                progress_callback(message)
        
    async def build_memory_bank(
        self, 
        config: BuildConfig,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> BuildResult:
        """
        Build a memory bank for the given repository
        
        Args:
            config: Build configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            BuildResult with build results
        """
        repo_path = Path(config.repo_path).resolve()
        
        # Validate repository path
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")
            
        # Use the explicit output path from config
        output_path = Path(config.output_path).resolve()
            
        # Create output directories
        output_path.mkdir(parents=True, exist_ok=True)
        memory_bank_dir = output_path / "memory-bank"
        memory_bank_dir.mkdir(exist_ok=True)
        tasks_dir = memory_bank_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        
        await self._call_progress_callback(progress_callback, "Directories created, loading system prompt...")
            
        # Load system prompt
        system_prompt = self._load_system_prompt(config.system_prompt_path)
        
        # Check for incremental update
        git_diff_file = repo_path / "git.diff"
        is_incremental = git_diff_file.exists() or config.mode == BuildMode.INCREMENTAL
        
        if is_incremental and git_diff_file.exists():
            prompt = self._create_incremental_prompt(system_prompt, git_diff_file, memory_bank_dir)
            mode = "incremental_update"
        else:
            prompt = self._create_full_build_prompt(system_prompt, memory_bank_dir)
            mode = "full_build"
            
        await self._call_progress_callback(progress_callback, f"Starting {mode} with Claude Code SDK...")
            
        # Build the memory bank
        try:
            files_written = await self._execute_claude_build(
                prompt=prompt,
                system_prompt=system_prompt,
                repo_path=repo_path,
                progress_callback=progress_callback,
                max_turns=config.max_turns
            )
            
            # Create metadata files
            await self._create_metadata_files(
                output_path=output_path,
                repo_path=repo_path,
                files_written=files_written,
                mode=mode
            )
            
            await self._call_progress_callback(progress_callback, "Memory bank building completed successfully!")
                
            return BuildResult(
                success=True,
                output_path=str(output_path),
                files_written=files_written,
                metadata={
                    "mode": mode,
                    "repo_path": str(repo_path),
                    "generated_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error during memory bank generation: {e}")
            await self._call_progress_callback(progress_callback, f"Error: {e}")
                
            return BuildResult(
                success=False,
                output_path=str(output_path),
                files_written=[],
                metadata={},
                errors=[str(e)]
            )
    
    def _load_system_prompt(self, custom_path: Optional[str] = None) -> str:
        """Load the system prompt for Claude Code"""
        if custom_path:
            prompt_path = Path(custom_path)
        else:
            prompt_path = self.system_prompt_path
            
        if not prompt_path.exists():
            logger.warning(f"System prompt not found: {prompt_path}")
            return "Analyze this codebase and create a comprehensive memory bank."
            
        with open(prompt_path, 'r') as f:
            return f.read()
    
    def _create_incremental_prompt(self, system_prompt: str, git_diff_file: Path, memory_bank_dir: Path) -> str:
        """Create prompt for incremental update"""
        git_diff_content = git_diff_file.read_text()
        return f"""{system_prompt}

INCREMENTAL UPDATE MODE: A git.diff file was found in the repository.

Git changes:
```diff
{git_diff_content}
```

TASK:
1. First, read the existing memory bank files at {memory_bank_dir} to understand the current state
2. Analyze the git changes to understand what has changed in the codebase
3. Update only the relevant memory bank files based on the changes
4. Create/update a changelog.md file at {memory_bank_dir}/changelog.md

INSTRUCTIONS:
- Read existing memory bank files first to understand current state
- Only update sections that are actually affected by the changes
- For small changes, make targeted updates rather than rewriting entire sections
- Use the Write tool to update the memory bank files
- Create/update changelog.md with this format:

## [{datetime.now().strftime('%Y-%m-%d %H:%M')}] - Update Summary
### Changes Made
- Brief description of code changes
- Impact on memory bank sections

### Memory Bank Updates
- List of files updated
- Summary of changes made

### Files Changed in Codebase
- List of files from the git diff

Be thorough but efficient - only update what actually needs updating."""

    def _create_full_build_prompt(self, system_prompt: str, memory_bank_dir: Path) -> str:
        """Create prompt for full build"""
        return f"""{system_prompt}

Analyze this codebase thoroughly and create a complete memory bank.

First, explore the codebase using LS, Read, Grep, and Glob tools to understand the project structure, technologies, and current state.

Then, use the Write tool to create each of the following files in {memory_bank_dir}:

1. {memory_bank_dir}/projectbrief.md - Project overview, core requirements, main goals
2. {memory_bank_dir}/productContext.md - Why this exists, problems solved, user goals  
3. {memory_bank_dir}/systemPatterns.md - Architecture, patterns, component relationships
4. {memory_bank_dir}/techContext.md - Technologies, frameworks, dependencies, setup
5. {memory_bank_dir}/activeContext.md - Current focus, recent changes, next steps
6. {memory_bank_dir}/progress.md - What works, what's pending, known issues
7. {memory_bank_dir}/tasks/_index.md - Task index with sections: In Progress, Pending, Completed, Abandoned

Analyze the codebase thoroughly before writing. Each file should contain comprehensive, accurate information based on your analysis."""

    async def _execute_claude_build(
        self,
        prompt: str,
        system_prompt: str,
        repo_path: Path,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_turns: int = 20
    ) -> List[str]:
        """Execute the Claude Code SDK build process"""
        
        # Configure Claude Code options
        options = ClaudeCodeOptions(
            max_turns=max_turns,
            system_prompt=system_prompt,
            cwd=str(repo_path),
            allowed_tools=["Read", "Grep", "Glob", "LS", "Write"],
            permission_mode="acceptEdits"
        )
        
        files_written = []
        
        # Stream messages from Claude Code
        async for message in query(prompt=prompt, options=options):
            # Handle different message types
            if hasattr(message, 'content'):
                content = message.content
                
                # Handle AssistantMessage with content blocks
                if isinstance(content, list):
                    for block in content:
                        # Log text messages
                        if hasattr(block, 'text'):
                            text = block.text
                            if text.strip():
                                await self._call_progress_callback(progress_callback, f"Claude: {text[:100]}..." if len(text) > 100 else f"Claude: {text}")
                        
                        # Track Write tool usage
                        elif hasattr(block, 'name') and hasattr(block, 'input'):
                            if block.name == "Write":
                                file_path = block.input.get('file_path', '')
                                await self._call_progress_callback(progress_callback, f"Writing file: {file_path}")
                                files_written.append(file_path)
                            else:
                                await self._call_progress_callback(progress_callback, f"Using tool: {block.name}")
        
        return files_written

    async def _create_metadata_files(
        self,
        output_path: Path,
        repo_path: Path,
        files_written: List[str],
        mode: str
    ):
        """Create metadata files for the memory bank"""
        
        # Create graph structure
        graph_path = output_path / "graph.json"
        graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "source_path": str(repo_path),
                "generator": "pc_cortex_core_builder",
                "files_written": files_written
            }
        }
        with open(graph_path, 'w') as f:
            json.dump(graph, f, indent=2)
        
        # Save generation summary
        summary_path = output_path / "generation_summary.json"
        summary = {
            "generated_at": datetime.now().isoformat(),
            "repo_path": str(repo_path),
            "files_written": files_written,
            "method": f"claude_core_builder_{mode}"
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)