"""
Claude Code SDK Integration Service
Provides a clean interface for Claude Code SDK within the backend
"""

import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from pathlib import Path

try:
    from claude_code_sdk import query, ClaudeCodeOptions, Message
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    logging.warning("Claude Code SDK not available. Install with: pip install claude-code-sdk")

logger = logging.getLogger(__name__)


class ClaudeIntegrationService:
    """Wrapper service for Claude Code SDK integration"""
    
    def __init__(self):
        if not CLAUDE_SDK_AVAILABLE:
            raise ImportError(
                "Claude Code SDK is not installed. "
                "Please install it with: pip install claude-code-sdk"
            )
    
    async def analyze_repository(
        self,
        prompt: str,
        repo_path: Path,
        system_prompt: Optional[str] = None,
        max_turns: int = 200,
        allowed_tools: Optional[List[str]] = None,
        permission_mode: str = "bypassPermissions"
    ) -> AsyncGenerator[Message, None]:
        """
        Analyze a repository using Claude Code SDK
        
        Args:
            prompt: The prompt to send to Claude
            repo_path: Path to the repository to analyze
            system_prompt: Optional system prompt
            max_turns: Maximum conversation turns
            allowed_tools: List of allowed tools (default: all)
            permission_mode: Permission mode for file operations
            
        Yields:
            Messages from Claude Code SDK
        """
        if allowed_tools is None:
            allowed_tools = ["Read", "Grep", "Glob", "LS", "Write"]
            
        options = ClaudeCodeOptions(
            max_turns=max_turns,
            system_prompt=system_prompt or self._default_system_prompt(),
            cwd=str(repo_path),
            allowed_tools=allowed_tools,
            permission_mode=permission_mode
        )
        
        logger.info(f"Starting Claude analysis of repository: {repo_path}")
        logger.debug(f"Options: max_turns={max_turns}, tools={allowed_tools}")
        
        try:
            async for message in query(prompt=prompt, options=options):
                yield message
        except Exception as e:
            logger.error(f"Error during Claude analysis: {e}")
            raise
    
    def parse_message_content(self, message: Message) -> Dict[str, Any]:
        """
        Parse a Claude message into a structured format
        
        Args:
            message: Message from Claude Code SDK
            
        Returns:
            Parsed message data
        """
        result = {
            "type": type(message).__name__,
            "content": [],
            "tools_used": []
        }
        
        if hasattr(message, 'content'):
            content = message.content
            
            if isinstance(content, list):
                for block in content:
                    # Handle text content
                    if hasattr(block, 'text'):
                        result["content"].append({
                            "type": "text",
                            "text": block.text
                        })
                    
                    # Handle tool usage
                    elif hasattr(block, 'name') and hasattr(block, 'input'):
                        tool_data = {
                            "name": block.name,
                            "input": block.input
                        }
                        result["tools_used"].append(tool_data)
                        
                        # Special handling for Write tool
                        if block.name == "Write":
                            result["content"].append({
                                "type": "file_write",
                                "file_path": block.input.get('file_path', ''),
                                "preview": block.input.get('content', '')[:100] + "..."
                            })
            elif isinstance(content, str):
                result["content"].append({
                    "type": "text",
                    "text": content
                })
        
        return result
    
    def extract_written_files(self, messages: List[Message]) -> List[str]:
        """
        Extract list of files written from Claude messages
        
        Args:
            messages: List of messages from Claude
            
        Returns:
            List of file paths that were written
        """
        written_files = []
        
        for message in messages:
            parsed = self.parse_message_content(message)
            for tool in parsed.get("tools_used", []):
                if tool["name"] == "Write":
                    file_path = tool["input"].get("file_path", "")
                    if file_path:
                        written_files.append(file_path)
        
        return written_files
    
    def _default_system_prompt(self) -> str:
        """Default system prompt if none provided"""
        return """You are an AI assistant helping to analyze and document a codebase. 
Your goal is to create comprehensive memory bank documentation that captures:
- Project structure and architecture
- Technologies and dependencies
- Current state and progress
- Tasks and future work
Be thorough, accurate, and well-organized in your analysis."""
    
    async def test_connection(self) -> bool:
        """Test if Claude Code SDK is properly configured"""
        try:
            # Simple test query
            test_prompt = "Say 'Hello' and nothing else"
            options = ClaudeCodeOptions(
                max_turns=1,
                allowed_tools=[],  # No tools needed for test
                permission_mode="none"
            )
            
            async for message in query(prompt=test_prompt, options=options):
                if message:
                    logger.info("Claude Code SDK connection test successful")
                    return True
                    
            return False
        except Exception as e:
            logger.error(f"Claude Code SDK connection test failed: {e}")
            return False
