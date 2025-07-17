#!/usr/bin/env python3
"""
Update Memory Bank based on git changes
Let Claude analyze the changes and update the memory bank accordingly
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions, Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryBankUpdater:
    """Updates memory bank based on git changes"""
    
    def __init__(self, repo_path: Path, memory_bank_path: Path):
        self.repo_path = repo_path.resolve()
        self.memory_bank_path = memory_bank_path.resolve()
        
    def validate_inputs(self) -> bool:
        """Validate inputs"""
        if not self.repo_path.exists():
            logger.error(f"Repository path does not exist: {self.repo_path}")
            return False
            
        if not self.memory_bank_path.exists():
            logger.error(f"Memory bank path does not exist: {self.memory_bank_path}")
            return False
            
        return True
    
    async def update_from_diff(self, diff_content: str) -> bool:
        """Update memory bank based on git diff"""
        
        # Prepare prompt for Claude
        prompt = f"""You are updating an existing memory bank based on code changes. 

Here are the git changes:
```diff
{diff_content}
```

Current memory bank is located at: {self.memory_bank_path}

TASK:
1. Read the current memory bank files to understand the current state
2. Analyze the git changes to understand what has changed in the codebase
3. Update the relevant memory bank files based on the changes
4. Write a changelog entry documenting what was updated and why

INSTRUCTIONS:
- Read existing memory bank files first to understand current state
- Only update sections that are actually affected by the changes
- For small changes, make targeted updates rather than rewriting entire sections
- Use the Write tool to update the memory bank files
- Create/update a changelog.md file in the memory bank directory with this format:

## [Date] - Update Summary
### Changes Made
- Brief description of code changes
- Impact on memory bank sections

### Memory Bank Updates
- List of files updated
- Summary of changes made

### Files Changed in Codebase
- List of files from the git diff

Be thorough but efficient - only update what actually needs updating."""

        # Configure Claude Code options
        options = ClaudeCodeOptions(
            max_turns=15,
            cwd=str(self.repo_path),
            allowed_tools=["Read", "Write", "Glob", "LS"],
            permission_mode="acceptEdits"
        )
        
        logger.info("Updating memory bank based on changes...")
        logger.info(f"Working directory: {self.repo_path}")
        logger.info(f"Memory bank location: {self.memory_bank_path}")
        
        try:
            messages: List[Message] = []
            files_updated = []
            
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
                                    logger.info(f"Updating file: {file_path}")
                                    files_updated.append(file_path)
                                else:
                                    logger.info(f"Using tool: {block.name}")
            
            logger.info(f"Update complete. Processed {len(messages)} messages.")
            logger.info(f"Files updated: {len(files_updated)}")
            
            # Save update summary
            self.save_update_summary(diff_content, files_updated)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during memory bank update: {e}")
            return False
    
    def save_update_summary(self, diff_content: str, files_updated: list):
        """Save update summary for tracking"""
        summary_path = self.memory_bank_path.parent / "update_summary.json"
        
        # Count changes in diff
        lines = diff_content.split('\n')
        files_changed = [line.split(' ')[0] for line in lines if line.startswith('diff --git')]
        
        summary = {
            "updated_at": datetime.now().isoformat(),
            "files_changed_in_code": files_changed,
            "memory_bank_files_updated": files_updated,
            "total_diff_lines": len(lines),
            "update_method": "claude_code_incremental"
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Update summary saved to: {summary_path}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Update memory bank based on git changes",
        epilog="Example: python3 update_memory_bank.py /path/to/repo /path/to/memory_bank --diff-file changes.diff"
    )
    parser.add_argument(
        "repo_path",
        type=Path,
        help="Path to the repository"
    )
    parser.add_argument(
        "memory_bank_path", 
        type=Path,
        help="Path to the memory bank directory"
    )
    parser.add_argument(
        "--diff-file",
        type=Path,
        help="File containing git diff content"
    )
    parser.add_argument(
        "--diff-stdin",
        action="store_true",
        help="Read git diff from stdin"
    )
    parser.add_argument(
        "--since-commit",
        type=str,
        help="Generate diff since specific commit"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get diff content
    diff_content = ""
    
    if args.diff_file:
        if not args.diff_file.exists():
            logger.error(f"Diff file does not exist: {args.diff_file}")
            sys.exit(1)
        diff_content = args.diff_file.read_text()
        
    elif args.diff_stdin:
        diff_content = sys.stdin.read()
        
    elif args.since_commit:
        import subprocess
        try:
            result = subprocess.run(
                ["git", "diff", args.since_commit],
                cwd=args.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Git diff failed: {result.stderr}")
                sys.exit(1)
            diff_content = result.stdout
        except Exception as e:
            logger.error(f"Error running git diff: {e}")
            sys.exit(1)
    
    else:
        logger.error("Must provide diff content via --diff-file, --diff-stdin, or --since-commit")
        sys.exit(1)
    
    if not diff_content.strip():
        logger.info("No changes found in diff")
        sys.exit(0)
    
    # Create updater and run
    updater = MemoryBankUpdater(args.repo_path, args.memory_bank_path)
    
    if not updater.validate_inputs():
        sys.exit(1)
    
    success = await updater.update_from_diff(diff_content)
    
    if success:
        logger.info("✅ Memory bank updated successfully!")
    else:
        logger.error("❌ Memory bank update failed!")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())