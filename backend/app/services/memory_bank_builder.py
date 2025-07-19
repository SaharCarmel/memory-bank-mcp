"""
Memory Bank Builder Service
Integrates memory bank building logic directly into the backend
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions, Message

logger = logging.getLogger(__name__)


class MemoryBankBuilder:
    """Builds memory banks using Claude Code SDK directly in the backend"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.system_prompt_path = root_path / "system_prompt.md"
        
    async def build_memory_bank(
        self, 
        repo_path: str, 
        output_name: Optional[str] = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Build a memory bank for the given repository
        
        Args:
            repo_path: Path to the repository to analyze
            output_name: Optional custom name for the output directory
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with build results
        """
        repo_path = Path(repo_path).resolve()
        
        # Validate repository path
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")
            
        # Determine output path
        if output_name:
            output_path = self.root_path / output_name
        else:
            folder_name = repo_path.name if repo_path.name else "repo"
            output_path = self.root_path / f"{folder_name}_memory_bank"
            
        # Create output directories
        output_path.mkdir(parents=True, exist_ok=True)
        memory_bank_dir = output_path / "memory-bank"
        memory_bank_dir.mkdir(exist_ok=True)
        tasks_dir = memory_bank_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        
        if progress_callback:
            await progress_callback("Directories created, loading system prompt...")
            
        # Load system prompt
        system_prompt = self._load_system_prompt()
        
        # Check for incremental update
        git_diff_file = repo_path / "git.diff"
        is_incremental = git_diff_file.exists()
        
        if is_incremental:
            prompt = self._create_incremental_prompt(system_prompt, git_diff_file, memory_bank_dir)
            mode = "incremental_update"
        else:
            prompt = self._create_full_build_prompt(system_prompt, memory_bank_dir)
            mode = "full_build"
            
        if progress_callback:
            await progress_callback(f"Starting {mode} with Claude Code SDK...")
            # Log the system prompt being used
            await progress_callback(f"[SYSTEM_PROMPT] Using system prompt from: {self.system_prompt_path}")
            await progress_callback(f"[SYSTEM_PROMPT_CONTENT] {system_prompt[:500]}..." if len(system_prompt) > 500 else f"[SYSTEM_PROMPT_CONTENT] {system_prompt}")
            # Log the full prompt being sent to Claude
            await progress_callback(f"[FULL_PROMPT] {prompt[:500]}..." if len(prompt) > 500 else f"[FULL_PROMPT] {prompt}")
            
        # Build the memory bank
        files_written = await self._execute_claude_build(
            prompt=prompt,
            system_prompt=system_prompt,
            repo_path=repo_path,
            progress_callback=progress_callback
        )
        
        # Create metadata files
        await self._create_metadata_files(
            output_path=output_path,
            repo_path=repo_path,
            files_written=files_written,
            mode=mode
        )
        
        if progress_callback:
            await progress_callback("Memory bank build completed successfully!")
            
        return {
            "success": True,
            "output_path": str(output_path),
            "files_written": files_written,
            "mode": mode,
            "timestamp": datetime.now().isoformat()
        }
    
    async def update_memory_bank(
        self,
        repo_path: str,
        memory_bank_name: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Update an existing memory bank
        
        Args:
            repo_path: Path to the repository
            memory_bank_name: Name of the memory bank to update
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with update results
        """
        memory_bank_path = self.root_path / memory_bank_name
        
        if not memory_bank_path.exists():
            raise ValueError(f"Memory bank does not exist: {memory_bank_name}")
            
        # For updates, we'll analyze recent changes and update accordingly
        # This is similar to build but with focus on changes
        return await self.build_memory_bank(
            repo_path=repo_path,
            output_name=memory_bank_name,
            progress_callback=progress_callback
        )
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt for Claude Code"""
        if not self.system_prompt_path.exists():
            logger.warning(f"System prompt not found: {self.system_prompt_path}")
            return "You are an AI assistant helping to build a memory bank for a codebase."
            
        with open(self.system_prompt_path, 'r') as f:
            return f.read()
    
    def _create_incremental_prompt(
        self, 
        system_prompt: str, 
        git_diff_file: Path, 
        memory_bank_dir: Path
    ) -> str:
        """Create prompt for incremental updates"""
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
    
    def _create_full_build_prompt(
        self, 
        system_prompt: str, 
        memory_bank_dir: Path
    ) -> str:
        """Create prompt for full memory bank build"""
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
        progress_callback=None
    ) -> List[str]:
        """Execute the Claude Code SDK build process"""
        # Configure Claude Code options
        options = ClaudeCodeOptions(
            max_turns=20,
            system_prompt=system_prompt,
            cwd=str(repo_path),
            allowed_tools=["Read", "Grep", "Glob", "LS", "Write"],
            permission_mode="acceptEdits"
        )
        
        messages: List[Message] = []
        files_written = []
        
        try:
            # Stream messages from Claude Code
            async for message in query(prompt=prompt, options=options):
                messages.append(message)
                
                # Handle different message types
                if hasattr(message, 'content'):
                    content = message.content
                    
                    # Handle AssistantMessage with content blocks
                    if isinstance(content, list):
                        for block in content:
                            # Log text messages with more detail
                            if hasattr(block, 'text'):
                                text = block.text
                                if text.strip() and progress_callback:
                                    # Capture full text for detailed analysis
                                    lines = text.strip().split('\n')
                                    
                                    # Detect and log key decision points
                                    for line in lines:
                                        if any(keyword in line.lower() for keyword in ['analyzing', 'found', 'creating', 'updating', 'exploring', 'understanding']):
                                            await progress_callback(f"[ANALYSIS] {line[:200]}")
                                    
                                    # Still provide general preview
                                    preview = text[:150] + "..." if len(text) > 150 else text
                                    await progress_callback(f"Claude: {preview}")
                            
                            # Track tool usage with more detail
                            elif hasattr(block, 'name') and hasattr(block, 'input'):
                                tool_name = block.name
                                tool_input = block.input
                                
                                if tool_name == "Write":
                                    file_path = tool_input.get('file_path', '')
                                    files_written.append(file_path)
                                    if progress_callback:
                                        await progress_callback(f"[WRITE] Creating/updating file: {file_path}")
                                        # Log first 100 chars of content being written
                                        content_preview = tool_input.get('content', '')[:100]
                                        if content_preview:
                                            await progress_callback(f"[CONTENT] {content_preview}...")
                                
                                elif tool_name == "Read":
                                    file_path = tool_input.get('file_path', '')
                                    if progress_callback:
                                        await progress_callback(f"[READ] Examining file: {file_path}")
                                
                                elif tool_name == "Grep":
                                    pattern = tool_input.get('pattern', '')
                                    path = tool_input.get('path', '.')
                                    if progress_callback:
                                        await progress_callback(f"[SEARCH] Searching for '{pattern}' in {path}")
                                
                                elif tool_name == "Glob":
                                    pattern = tool_input.get('pattern', '')
                                    if progress_callback:
                                        await progress_callback(f"[GLOB] Finding files matching: {pattern}")
                                
                                elif tool_name == "LS":
                                    path = tool_input.get('path', '.')
                                    if progress_callback:
                                        await progress_callback(f"[LS] Listing directory: {path}")
                                
                                else:
                                    if progress_callback:
                                        await progress_callback(f"[TOOL] Using {tool_name} with params: {str(tool_input)[:100]}")
            
            if progress_callback:
                await progress_callback(f"Analysis complete. Files written: {len(files_written)}")
                
            return files_written
            
        except Exception as e:
            logger.error(f"Error during Claude build: {e}")
            raise
    
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
                "generator": "pc_cortex_backend",
                "files_written": files_written,
                "mode": mode
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
            "num_files": len(files_written),
            "method": "backend_integrated",
            "mode": mode
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)