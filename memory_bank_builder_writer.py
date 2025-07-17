#!/usr/bin/env python3
"""
Memory Bank Builder that lets Claude write files directly
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions, Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WriterMemoryBankBuilder:
    """Builds memory banks by letting Claude write files directly"""
    
    def __init__(self, repo_path: Path, output_path: Path):
        self.repo_path = repo_path.resolve()
        self.output_path = output_path.resolve()
        self.system_prompt_path = Path(__file__).parent / "system_prompt.md"
        
    def validate_inputs(self) -> bool:
        """Validate repository path and create output directory"""
        if not self.repo_path.exists():
            logger.error(f"Repository path does not exist: {self.repo_path}")
            return False
            
        if not self.repo_path.is_dir():
            logger.error(f"Repository path is not a directory: {self.repo_path}")
            return False
            
        # Create output directory if it doesn't exist
        self.output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ready: {self.output_path}")
        
        return True
    
    def load_system_prompt(self) -> str:
        """Load the system prompt for Claude Code"""
        if not self.system_prompt_path.exists():
            logger.error(f"System prompt not found: {self.system_prompt_path}")
            return ""
            
        with open(self.system_prompt_path, 'r') as f:
            return f.read()
    
    async def build(self) -> bool:
        """Execute the memory bank building process"""
        logger.info(f"Building memory bank for: {self.repo_path}")
        logger.info(f"Output directory: {self.output_path}")
        
        # Validate inputs
        if not self.validate_inputs():
            return False
        
        # Create memory-bank subdirectory
        memory_bank_dir = self.output_path / "memory-bank"
        memory_bank_dir.mkdir(exist_ok=True)
        
        # Create tasks subdirectory
        tasks_dir = memory_bank_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        
        system_prompt = self.load_system_prompt()
        
        # Check if git.diff file exists for incremental updates
        git_diff_file = self.repo_path / "git.diff"
        
        if git_diff_file.exists():
            # Incremental update mode
            git_diff_content = git_diff_file.read_text()
            prompt = f"""{system_prompt}

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
        else:
            # Full creation mode
            prompt = f"""{system_prompt}

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
        
        # Configure Claude Code options
        options = ClaudeCodeOptions(
            max_turns=20,  # Allow enough turns for analysis and writing
            system_prompt=system_prompt,
            cwd=str(self.repo_path),  # Set working directory to the repo
            allowed_tools=["Read", "Grep", "Glob", "LS", "Write"],  # Include Write tool
            permission_mode="acceptEdits"  # Auto-accept file writes
        )
        
        logger.info("Invoking Claude Code SDK with Write permissions...")
        logger.info(f"Working directory: {self.repo_path}")
        logger.info("Claude will analyze the codebase and write files directly...")
        
        try:
            messages: List[Message] = []
            files_written = []
            
            # Stream messages from Claude Code
            async for message in query(prompt=prompt, options=options):
                messages.append(message)
                
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
                                    logger.info(f"Claude: {text[:100]}..." if len(text) > 100 else f"Claude: {text}")
                            
                            # Track Write tool usage
                            elif hasattr(block, 'name') and hasattr(block, 'input'):
                                if block.name == "Write":
                                    file_path = block.input.get('file_path', '')
                                    logger.info(f"Writing file: {file_path}")
                                    files_written.append(file_path)
                                else:
                                    logger.info(f"Using tool: {block.name}")
            
            logger.info(f"Analysis complete. Processed {len(messages)} messages.")
            logger.info(f"Files written: {len(files_written)}")
            
            # Create graph structure
            graph_path = self.output_path / "graph.json"
            graph = {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat(),
                    "source_path": str(self.repo_path),
                    "generator": "pc_cortex_writer_builder",
                    "files_written": files_written
                }
            }
            with open(graph_path, 'w') as f:
                json.dump(graph, f, indent=2)
            logger.info(f"Created graph structure: {graph_path}")
            
            # Save generation summary
            summary_path = self.output_path / "generation_summary.json"
            summary = {
                "generated_at": datetime.now().isoformat(),
                "repo_path": str(self.repo_path),
                "files_written": files_written,
                "num_messages": len(messages),
                "method": "claude_direct_write"
            }
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info("Memory bank building completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error during memory bank generation: {e}")
            return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Build a memory bank by letting Claude write files directly"
    )
    parser.add_argument(
        "repo_path",
        type=Path,
        help="Path to the repository to analyze"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory for the memory bank (default: ./{repo_name}_memory_bank)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine output path
    if args.output is None:
        folder_name = args.repo_path.name if args.repo_path.name else "current"
        args.output = Path.cwd() / f"{folder_name}_memory_bank"
    
    # Create builder and run
    builder = WriterMemoryBankBuilder(args.repo_path, args.output)
    success = await builder.build()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())