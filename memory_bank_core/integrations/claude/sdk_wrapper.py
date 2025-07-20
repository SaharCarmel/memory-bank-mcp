"""
Claude Code SDK wrapper implementation
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from .interface import ClaudeIntegration
from ...interfaces.builder import BuildProgressCallback
from ...exceptions.build import ClaudeIntegrationError

logger = logging.getLogger(__name__)


class ClaudeCodeSDKWrapper(ClaudeIntegration):
    """Wrapper for Claude Code SDK"""
    
    def __init__(self, max_turns: int = 1000):
        self.max_turns = max_turns
        self._sdk_available = self._check_sdk_availability()
    
    def _check_sdk_availability(self) -> bool:
        """Check if Claude Code SDK is available"""
        try:
            from claude_code_sdk import query, ClaudeCodeOptions, Message
            return True
        except ImportError:
            logger.warning("Claude Code SDK not available")
            return False
    
    async def execute_build(
        self,
        prompt: str,
        system_prompt: str,
        repo_path: Path,
        progress_callback: Optional[BuildProgressCallback] = None
    ) -> List[str]:
        """Execute a memory bank build using Claude Code SDK"""
        if not self._sdk_available:
            raise ClaudeIntegrationError("Claude Code SDK is not available")
        
        try:
            from claude_code_sdk import query, ClaudeCodeOptions, Message
        except ImportError as e:
            raise ClaudeIntegrationError(f"Failed to import Claude Code SDK: {e}")
        
        # Configure Claude Code options
        options = ClaudeCodeOptions(
            max_turns=self.max_turns,
            system_prompt=system_prompt,
            cwd=str(repo_path),
            allowed_tools=self.get_allowed_tools(),
            permission_mode="bypassPermissions"
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
            raise ClaudeIntegrationError(f"Claude build failed: {e}")
    
    async def validate_integration(self) -> bool:
        """Validate that the Claude integration is properly configured"""
        return self._sdk_available
    
    def get_allowed_tools(self) -> List[str]:
        """Get the list of tools allowed for Claude operations"""
        return ["Read", "Grep", "Glob", "LS", "Write"]
    
    def configure_options(self, **kwargs) -> Dict[str, Any]:
        """Configure options for Claude execution"""
        options = {
            "max_turns": kwargs.get("max_turns", self.max_turns),
            "allowed_tools": kwargs.get("allowed_tools", self.get_allowed_tools()),
            "permission_mode": kwargs.get("permission_mode", "bypassPermissions")
        }
        return options
