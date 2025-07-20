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
        
        await self._call_progress_callback(progress_callback, "Setting up directories and loading system prompt...")
            
        # Load system prompt
        system_prompt = self._load_system_prompt(config.system_prompt_path)
        
        # Check for incremental update
        git_diff_file = repo_path / "git.diff"
        is_incremental = git_diff_file.exists() or config.mode == BuildMode.INCREMENTAL
        
        if is_incremental and git_diff_file.exists():
            await self._call_progress_callback(progress_callback, f"Found git diff - running incremental update")
            prompt = self._create_incremental_prompt(system_prompt, git_diff_file, memory_bank_dir)
            mode = "incremental_update"
        else:
            await self._call_progress_callback(progress_callback, "Running full memory bank build")
            prompt = self._create_full_build_prompt(system_prompt, memory_bank_dir)
            mode = "full_build"
            
        await self._call_progress_callback(progress_callback, f"Starting {mode}...")
            
        # Build the memory bank with restart logic
        try:
            files_written = await self._execute_claude_build_with_restart(
                prompt=prompt,
                system_prompt=system_prompt,
                repo_path=repo_path,
                progress_callback=progress_callback,
                config=config
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
            logger.warning(f"System prompt not found: {prompt_path} - using fallback")
            return "Analyze this codebase and create a comprehensive memory bank."
            
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading system prompt: {e} - using fallback")
            return "Analyze this codebase and create a comprehensive memory bank."
    
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

    async def _execute_claude_build_with_restart(
        self,
        prompt: str,
        system_prompt: str,
        repo_path: Path,
        progress_callback: Optional[Callable[[str], None]] = None,
        config: BuildConfig = None
    ) -> List[str]:
        """Execute Claude build with restart logic for early termination"""
        
        if config is None:
            # Fallback to basic execution without restart
            return await self._execute_claude_build(prompt, system_prompt, repo_path, progress_callback, 1000)
        
        all_files_written = []
        attempt = 1
        previous_file_count = 0
        
        while attempt <= config.max_restart_attempts:
            await self._call_progress_callback(progress_callback, f"[ATTEMPT {attempt}] Starting memory bank build attempt...")
            
            try:
                files_written = await self._execute_claude_build(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    repo_path=repo_path,
                    progress_callback=progress_callback,
                    max_turns=config.max_turns,
                    config=config
                )
                
                # Add newly written files to the total
                for file_path in files_written:
                    if file_path not in all_files_written:
                        all_files_written.append(file_path)
                
                # Check if we got a sufficient result
                if len(files_written) > 0:
                    await self._call_progress_callback(progress_callback, f"[ATTEMPT {attempt}] Successfully created {len(files_written)} files")
                    
                    # Check if we have core memory bank files
                    memory_bank_dir = Path(config.output_path) / "memory-bank"
                    core_files = ["projectbrief.md", "productContext.md", "systemPatterns.md", "techContext.md"]
                    existing_core_files = []
                    
                    for core_file in core_files:
                        file_path = memory_bank_dir / core_file
                        if file_path.exists():
                            existing_core_files.append(core_file)
                    
                    if len(existing_core_files) >= 2:  # At least 2 core files created
                        await self._call_progress_callback(progress_callback, f"[SUCCESS] Memory bank build completed with {len(existing_core_files)} core files")
                        return all_files_written
                    else:
                        await self._call_progress_callback(progress_callback, f"[ATTEMPT {attempt}] Only {len(existing_core_files)} core files created, may need restart")
                
                # Check if conversation terminated early (likely at 40 turns)
                if config.auto_restart_on_early_termination and len(files_written) == 0:
                    # Check if we're making progress between attempts
                    current_total_files = len(all_files_written)
                    if current_total_files == previous_file_count and attempt > 1:
                        await self._call_progress_callback(progress_callback, f"[ABORT] No progress made since last attempt ({current_total_files} files), stopping restarts")
                        return all_files_written
                    
                    if attempt < config.max_restart_attempts:
                        await self._call_progress_callback(progress_callback, f"[RESTART] No files created in attempt {attempt}, restarting... (attempt {attempt + 1}/{config.max_restart_attempts})")
                        await self._call_progress_callback(progress_callback, f"[RESTART] Reason: auto_restart_on_early_termination=True, files_written=0")
                        
                        # Create a continuation prompt that builds on existing work
                        continuation_prompt = self._create_continuation_prompt(
                            original_prompt=prompt,
                            memory_bank_dir=memory_bank_dir,
                            attempt=attempt + 1
                        )
                        prompt = continuation_prompt
                        previous_file_count = current_total_files
                        attempt += 1
                        continue
                    else:
                        await self._call_progress_callback(progress_callback, f"[EXHAUSTED] Maximum restart attempts reached ({config.max_restart_attempts})")
                        return all_files_written
                elif len(existing_core_files) < 2 and len(files_written) > 0:
                    # Some files created but not enough core files
                    if attempt < config.max_restart_attempts:
                        await self._call_progress_callback(progress_callback, f"[RESTART] Insufficient core files ({len(existing_core_files)}/4), restarting... (attempt {attempt + 1}/{config.max_restart_attempts})")
                        await self._call_progress_callback(progress_callback, f"[RESTART] Files created: {len(files_written)}, Core files: {existing_core_files}")
                        
                        # Create a continuation prompt focused on missing core files
                        continuation_prompt = self._create_continuation_prompt(
                            original_prompt=prompt,
                            memory_bank_dir=memory_bank_dir,
                            attempt=attempt + 1
                        )
                        prompt = continuation_prompt
                        attempt += 1
                        continue
                    else:
                        await self._call_progress_callback(progress_callback, f"[EXHAUSTED] Maximum restart attempts reached, proceeding with {len(files_written)} files")
                        return all_files_written
                else:
                    # Normal completion
                    await self._call_progress_callback(progress_callback, f"[COMPLETION] Build completed normally: {len(files_written)} files, {len(existing_core_files)} core files")
                    return all_files_written
                    
            except Exception as e:
                await self._call_progress_callback(progress_callback, f"[ATTEMPT {attempt}] Error: {str(e)}")
                if attempt < config.max_restart_attempts:
                    await self._call_progress_callback(progress_callback, f"[RESTART] Retrying due to error... (attempt {attempt + 1}/{config.max_restart_attempts})")
                    attempt += 1
                    continue
                else:
                    raise e
        
        return all_files_written

    def _create_continuation_prompt(self, original_prompt: str, memory_bank_dir: Path, attempt: int) -> str:
        """Create a continuation prompt for restart attempts"""
        
        # Check what files already exist
        existing_files = []
        if memory_bank_dir.exists():
            for file_path in memory_bank_dir.rglob("*.md"):
                if file_path.is_file() and file_path.stat().st_size > 0:
                    existing_files.append(str(file_path.relative_to(memory_bank_dir)))
        
        if len(existing_files) > 0:
            continuation_prompt = f"""CONTINUATION ATTEMPT {attempt}: The previous conversation was cut short, but some files were already created.

Existing files in memory bank: {', '.join(existing_files)}

Please continue where the previous attempt left off. First, read the existing files to understand what's already been documented, then:

1. Check which memory bank files are missing or incomplete
2. Complete any missing core files: projectbrief.md, productContext.md, systemPatterns.md, techContext.md, activeContext.md, progress.md
3. Ensure all files have comprehensive content based on the codebase analysis

{original_prompt}

IMPORTANT: This is a continuation - read existing files first before creating new ones."""
        else:
            continuation_prompt = f"""RESTART ATTEMPT {attempt}: Previous conversation was cut short with no files created.

{original_prompt}

IMPORTANT: This is attempt {attempt} - please work efficiently to create the core memory bank files."""
        
        return continuation_prompt

    async def _execute_claude_build(
        self,
        prompt: str,
        system_prompt: str,
        repo_path: Path,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_turns: int = 1000,
        config: Optional[BuildConfig] = None
    ) -> List[str]:
        """Execute the Claude Code SDK build process"""
        
        await self._call_progress_callback(progress_callback, "Initializing Claude Code SDK...")
        
        # Configure Claude Code options with configurable settings
        
        # Determine tool set based on configuration
        if config and config.use_minimal_tools:
            # Minimal tool set to reduce complexity
            allowed_tools = ["Read", "Glob", "LS", "Write"]
            await self._call_progress_callback(progress_callback, "Using minimal tool set to reduce complexity")
        else:
            # Full tool set for comprehensive analysis
            allowed_tools = ["Read", "Grep", "Glob", "LS", "Write", "Bash", "Edit", "MultiEdit", "Task", "TodoWrite"]
        
        # Determine permission mode
        permission_mode = config.permission_mode if config else "bypassPermissions"
        
        options = ClaudeCodeOptions(
            max_turns=max_turns,
            system_prompt=system_prompt,
            cwd=str(repo_path),
            allowed_tools=allowed_tools,
            permission_mode=permission_mode
        )
        
        await self._call_progress_callback(progress_callback, f"Starting memory bank generation with max {max_turns} turns...")
        await self._call_progress_callback(progress_callback, f"Working directory: {repo_path}")
        await self._call_progress_callback(progress_callback, f"SDK Configuration: tools={len(options.allowed_tools)}, permission_mode={options.permission_mode}")
        
        files_written = []
        message_count = 0
        last_message_type = None
        conversation_started = datetime.now()
        
        try:
            # Stream messages from Claude Code
            async for message in query(prompt=prompt, options=options):
                message_count += 1
                
                # Enhanced progress logging
                if message_count % 5 == 0:
                    elapsed = (datetime.now() - conversation_started).total_seconds()
                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] Processing message {message_count}... (elapsed: {elapsed:.1f}s)")
                
                # Log turn milestone warnings
                if message_count in [35, 38, 39]:
                    await self._call_progress_callback(progress_callback, f"[WARNING] Approaching turn {message_count} - potential SDK limit at 40")
                
                # Handle different message types
                if hasattr(message, 'content'):
                    last_message_type = "content"
                    content = message.content
                    
                    # Handle AssistantMessage with content blocks
                    if isinstance(content, list):
                        for block in content:
                            # Log text messages
                            if hasattr(block, 'text'):
                                text = block.text
                                if text.strip():
                                    preview = text[:100] + "..." if len(text) > 100 else text
                                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] Claude: {preview}")
                            
                            # Track tool usage
                            elif hasattr(block, 'name') and hasattr(block, 'input'):
                                tool_name = block.name
                                tool_input = block.input
                                
                                if tool_name == "Write":
                                    file_path = tool_input.get('file_path', 'unknown')
                                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] Creating file: {file_path}")
                                    files_written.append(file_path)
                                elif tool_name == "Read":
                                    file_path = tool_input.get('file_path', 'unknown')
                                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] Reading: {file_path}")
                                elif tool_name in ["Grep", "Glob"]:
                                    pattern = tool_input.get('pattern', 'unknown')
                                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] {tool_name} search: {pattern}")
                                elif tool_name == "LS":
                                    path = tool_input.get('path', 'current directory')
                                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] Listing: {path}")
                                else:
                                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] Using tool: {tool_name}")
                    else:
                        # Handle non-list content
                        await self._call_progress_callback(progress_callback, f"[TURN {message_count}] Non-block content: {type(content)}")
                
                # Handle error messages
                elif hasattr(message, 'error'):
                    last_message_type = "error"
                    error_msg = str(message.error)
                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] ERROR: {error_msg}")
                    logger.error(f"Claude Code SDK error at turn {message_count}: {error_msg}")
                else:
                    last_message_type = f"unknown_{type(message)}"
                    await self._call_progress_callback(progress_callback, f"[TURN {message_count}] Unknown message type: {type(message)}")
            
            # Conversation ended - analyze termination
            elapsed = (datetime.now() - conversation_started).total_seconds()
            await self._call_progress_callback(progress_callback, f"[TERMINATION] Conversation ended at turn {message_count} after {elapsed:.1f}s")
            await self._call_progress_callback(progress_callback, f"[TERMINATION] Last message type: {last_message_type}")
            await self._call_progress_callback(progress_callback, f"[TERMINATION] Files created: {len(files_written)}")
            
            # Check if this was an early termination
            if message_count < max_turns and message_count <= 40:
                await self._call_progress_callback(progress_callback, f"[WARNING] Conversation terminated early at turn {message_count} (expected max: {max_turns})")
                await self._call_progress_callback(progress_callback, f"[WARNING] This appears to be a Claude Code SDK limitation")
                
                # Log SDK version for debugging
                try:
                    import claude_code_sdk
                    version = getattr(claude_code_sdk, '__version__', 'unknown')
                    await self._call_progress_callback(progress_callback, f"[DEBUG] Claude Code SDK version: {version}")
                except:
                    await self._call_progress_callback(progress_callback, f"[DEBUG] Could not determine SDK version")
            
            if len(files_written) > 0:
                await self._call_progress_callback(progress_callback, f"Memory bank generation completed with {len(files_written)} files created")
            else:
                await self._call_progress_callback(progress_callback, f"Memory bank generation completed but no files were created - conversation may have terminated early")
            
        except Exception as e:
            elapsed = (datetime.now() - conversation_started).total_seconds()
            error_msg = f"Exception at turn {message_count} after {elapsed:.1f}s: {type(e).__name__}: {str(e)}"
            await self._call_progress_callback(progress_callback, error_msg)
            logger.error(error_msg)
            raise e
        
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
