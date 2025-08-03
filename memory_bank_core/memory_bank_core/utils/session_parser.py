"""
Claude Code Session Parser

Parses Claude Code JSONL session files to extract token usage information
for cost calculation and analysis.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re

from .cost_calculator import CostCalculator, ClaudeModel, TokenUsage

logger = logging.getLogger(__name__)


@dataclass
class SessionTokenUsage:
    """Token usage information from a Claude Code session"""
    session_id: str
    session_start: datetime
    session_end: datetime
    total_input_tokens: int
    total_output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    message_count: int
    model_used: str
    working_directory: str


class SessionParser:
    """Parses Claude Code JSONL session files"""
    
    def __init__(self):
        """Initialize the session parser"""
        self.claude_projects_dir = Path.home() / ".claude" / "projects"
        
    def find_project_sessions(self, project_path: str) -> List[Path]:
        """
        Find all session files for a specific project
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of session file paths
        """
        # Convert project path to Claude's naming convention
        # Replace / with - and _ with - (Claude normalizes underscores to hyphens)
        project_key = project_path.replace("/", "-").replace("_", "-")
        if not project_key.startswith("-"):
            project_key = "-" + project_key
        
        # Find matching project directory
        project_dirs = []
        if self.claude_projects_dir.exists():
            for dir_path in self.claude_projects_dir.iterdir():
                if dir_path.is_dir() and project_key in dir_path.name:
                    project_dirs.append(dir_path)
        
        # Collect all JSONL files from matching directories
        session_files = []
        for project_dir in project_dirs:
            for file_path in project_dir.glob("*.jsonl"):
                session_files.append(file_path)
        
        # Sort by modification time (newest first)
        session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return session_files
    
    def parse_session_file(self, session_file: Path) -> Optional[SessionTokenUsage]:
        """
        Parse a single JSONL session file to extract token usage
        
        Args:
            session_file: Path to the JSONL session file
            
        Returns:
            SessionTokenUsage object or None if parsing fails
        """
        try:
            with open(session_file, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return None
            
            # Parse session metadata from first line
            first_line = json.loads(lines[0])
            session_id = first_line.get("sessionId", session_file.stem)
            working_directory = first_line.get("cwd", "unknown")
            
            # Handle timestamp parsing with fallback
            timestamp_str = first_line.get("timestamp", "")
            if timestamp_str:
                try:
                    session_start = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    # Fallback to file modification time
                    session_start = datetime.fromtimestamp(session_file.stat().st_mtime, timezone.utc)
            else:
                # Use file modification time if no timestamp
                session_start = datetime.fromtimestamp(session_file.stat().st_mtime, timezone.utc)
            
            # Parse all lines to extract token usage
            total_input_tokens = 0
            total_output_tokens = 0
            total_cache_creation_tokens = 0
            total_cache_read_tokens = 0
            message_count = 0
            model_used = "unknown"
            session_end = session_start
            
            # Ensure session_start is timezone-aware for comparisons
            if session_start.tzinfo is None:
                session_start = session_start.replace(tzinfo=timezone.utc)
                session_end = session_start
            
            for line in lines:
                try:
                    data = json.loads(line)
                    
                    # Update session end time
                    if "timestamp" in data:
                        timestamp_str = data["timestamp"]
                        if timestamp_str:
                            try:
                                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                                if timestamp > session_end:
                                    session_end = timestamp
                            except (ValueError, AttributeError):
                                pass  # Skip invalid timestamps
                    
                    # Extract token usage from assistant messages
                    if (data.get("type") == "assistant" and 
                        "message" in data and 
                        "usage" in data["message"]):
                        
                        usage = data["message"]["usage"]
                        total_input_tokens += usage.get("input_tokens", 0)
                        total_output_tokens += usage.get("output_tokens", 0)
                        total_cache_creation_tokens += usage.get("cache_creation_input_tokens", 0)
                        total_cache_read_tokens += usage.get("cache_read_input_tokens", 0)
                        message_count += 1
                        
                        # Get model information
                        if "model" in data["message"]:
                            model_used = data["message"]["model"]
                
                except json.JSONDecodeError:
                    continue
            
            return SessionTokenUsage(
                session_id=session_id,
                session_start=session_start,
                session_end=session_end,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                cache_creation_tokens=total_cache_creation_tokens,
                cache_read_tokens=total_cache_read_tokens,
                message_count=message_count,
                model_used=model_used,
                working_directory=working_directory
            )
            
        except Exception as e:
            logger.error(f"Failed to parse session file {session_file}: {e}")
            return None
    
    def get_project_token_usage(
        self, 
        project_path: str, 
        time_filter: Optional[Tuple[datetime, datetime]] = None,
        session_limit: Optional[int] = None
    ) -> List[SessionTokenUsage]:
        """
        Get token usage for all sessions in a project
        
        Args:
            project_path: Path to the project directory
            time_filter: Optional tuple of (start_time, end_time) to filter sessions
            session_limit: Optional limit on number of sessions to parse
            
        Returns:
            List of SessionTokenUsage objects
        """
        session_files = self.find_project_sessions(project_path)
        
        if session_limit:
            session_files = session_files[:session_limit]
        
        session_usages = []
        
        for session_file in session_files:
            session_usage = self.parse_session_file(session_file)
            if session_usage:
                # Apply time filter if specified
                if time_filter:
                    start_time, end_time = time_filter
                    if not (start_time <= session_usage.session_start <= end_time):
                        continue
                
                session_usages.append(session_usage)
        
        return session_usages
    
    def calculate_project_cost(
        self, 
        project_path: str,
        model: ClaudeModel = ClaudeModel.CLAUDE_4_SONNET,
        time_filter: Optional[Tuple[datetime, datetime]] = None,
        session_limit: Optional[int] = None
    ) -> Tuple[CostCalculator, List[SessionTokenUsage]]:
        """
        Calculate total cost for a project based on session usage
        
        Args:
            project_path: Path to the project directory
            model: Claude model used (for pricing)
            time_filter: Optional time range filter
            session_limit: Optional limit on sessions to include
            
        Returns:
            Tuple of (CostCalculator with usage data, List of session usages)
        """
        session_usages = self.get_project_token_usage(
            project_path=project_path,
            time_filter=time_filter,
            session_limit=session_limit
        )
        
        calculator = CostCalculator(model)
        
        for session in session_usages:
            # Add token usage for each session
            calculator.add_token_usage(
                input_tokens=session.total_input_tokens + session.cache_creation_tokens,
                output_tokens=session.total_output_tokens,
                operation_name=f"session_{session.session_id[:8]}",
                component_name=None
            )
        
        return calculator, session_usages
    
    def analyze_recent_usage(
        self, 
        project_path: str,
        hours: int = 24,
        model: ClaudeModel = ClaudeModel.CLAUDE_4_SONNET
    ) -> Dict[str, Any]:
        """
        Analyze token usage for recent sessions
        
        Args:
            project_path: Path to the project directory
            hours: Number of hours to look back
            model: Claude model for cost calculation
            
        Returns:
            Dictionary with usage analysis
        """
        from datetime import timedelta
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        calculator, sessions = self.calculate_project_cost(
            project_path=project_path,
            model=model,
            time_filter=(start_time, end_time)
        )
        
        if not sessions:
            return {
                "period": f"Last {hours} hours",
                "sessions": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "message": "No sessions found in the specified period"
            }
        
        cost_breakdown = calculator.calculate_cost()
        
        # Calculate session statistics
        total_messages = sum(s.message_count for s in sessions)
        total_duration = sum((s.session_end - s.session_start).total_seconds() for s in sessions) / 3600  # hours
        
        return {
            "period": f"Last {hours} hours",
            "sessions": len(sessions),
            "total_messages": total_messages,
            "total_duration_hours": round(total_duration, 2),
            "total_input_tokens": cost_breakdown.total_input_tokens,
            "total_output_tokens": cost_breakdown.total_output_tokens,
            "total_tokens": cost_breakdown.total_tokens,
            "total_cost": round(cost_breakdown.total_cost, 4),
            "average_cost_per_session": round(cost_breakdown.total_cost / len(sessions), 4),
            "model_used": sessions[0].model_used if sessions else "unknown",
            "session_details": [
                {
                    "session_id": s.session_id[:8],
                    "start_time": s.session_start.isoformat(),
                    "duration_minutes": round((s.session_end - s.session_start).total_seconds() / 60, 1),
                    "messages": s.message_count,
                    "input_tokens": s.total_input_tokens + s.cache_creation_tokens,
                    "output_tokens": s.total_output_tokens
                }
                for s in sessions
            ]
        }


def detect_memory_bank_sessions(project_path: str) -> List[Dict[str, Any]]:
    """
    Detect which sessions were likely related to memory bank building
    based on session content and timing
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        List of session information dictionaries
    """
    parser = SessionParser()
    sessions = parser.get_project_token_usage(project_path)
    
    memory_bank_sessions = []
    
    for session in sessions:
        # Check if session is recent (within last few days for multi-agent work)
        # Make sure both datetimes have timezone info for comparison
        now = datetime.now(timezone.utc)
        session_start = session.session_start
        if session_start.tzinfo is None:
            session_start = session_start.replace(tzinfo=timezone.utc)
        days_old = (now - session_start).days
        
        # Look for sessions with high token usage (likely multi-agent builds)
        total_tokens = session.total_input_tokens + session.total_output_tokens
        
        # Sessions with >50k tokens and recent are likely memory bank builds
        if total_tokens > 50000 or session.message_count > 100:
            calculator = CostCalculator()
            calculator.add_token_usage(
                session.total_input_tokens + session.cache_creation_tokens,
                session.total_output_tokens,
                f"session_{session.session_id[:8]}"
            )
            cost = calculator.calculate_cost().total_cost
            
            memory_bank_sessions.append({
                "session_id": session.session_id[:8],
                "start_time": session.session_start,
                "duration_hours": (session.session_end - session.session_start).total_seconds() / 3600,
                "days_old": days_old,
                "total_tokens": total_tokens,
                "messages": session.message_count,
                "estimated_cost": round(cost, 4),
                "model": session.model_used,
                "likely_memory_bank_session": total_tokens > 50000
            })
    
    # Sort by token usage (highest first)
    memory_bank_sessions.sort(key=lambda x: x["total_tokens"], reverse=True)
    
    return memory_bank_sessions