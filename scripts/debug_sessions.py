#!/usr/bin/env python3
"""
Debug session detection
"""

import sys
from pathlib import Path

# Add path for imports
sys.path.append(str(Path(__file__).parent))

from memory_bank_core.utils.session_parser import SessionParser


def debug_session_detection():
    """Debug why session detection isn't working"""
    
    project_path = "/Users/saharcarmel/Code/personal/future/pc_cortex"
    parser = SessionParser()
    
    print("🔍 Debugging Session Detection")
    print("=" * 50)
    print(f"Project Path: {project_path}")
    print(f"Claude Projects Dir: {parser.claude_projects_dir}")
    print(f"Directory exists: {parser.claude_projects_dir.exists()}")
    
    # Show what the project key conversion looks like - use same logic as session parser
    project_key = project_path.replace("/", "-").replace("_", "-")
    if not project_key.startswith("-"):
        project_key = "-" + project_key
    print(f"Project Key: {project_key}")
    
    # List all project directories in Claude
    print(f"\nClaude Project Directories:")
    found_match = False
    if parser.claude_projects_dir.exists():
        for dir_path in parser.claude_projects_dir.iterdir():
            if dir_path.is_dir():
                matches = project_key in dir_path.name
                status = "✅ MATCHES" if matches else "  "
                print(f"  {status} {dir_path.name}")
                if matches:
                    found_match = True
                    print(f"        Has {len(list(dir_path.glob('*.jsonl')))} JSONL files")
    
    print(f"\nProject Key Match Found: {found_match}")
    
    # Try to find sessions
    print(f"\nLooking for sessions...")
    session_files = parser.find_project_sessions(project_path)
    print(f"Found {len(session_files)} session files")
    
    # Try parsing some sessions
    if session_files:
        print(f"\nTesting session parsing...")
        for i, session_file in enumerate(session_files[:3]):  # Test first 3
            print(f"  {i+1}. {session_file.name} ({session_file.stat().st_size} bytes)")
            
            # Try to parse it
            session_usage = parser.parse_session_file(session_file)
            if session_usage:
                total_tokens = session_usage.total_input_tokens + session_usage.total_output_tokens
                print(f"     ✅ Parsed: {total_tokens:,} tokens, {session_usage.message_count} messages")
                print(f"     📅 Date: {session_usage.session_start}")
                print(f"     🏷️  Model: {session_usage.model_used}")
                
                # Check if it would qualify as memory bank session
                if total_tokens > 50000 or session_usage.message_count > 100:
                    print(f"     🤖 Would qualify as memory bank session!")
                else:
                    print(f"     ⚠️  Below threshold for memory bank session")
            else:
                print(f"     ❌ Failed to parse")
    
    # Test the full detection
    print(f"\nTesting full memory bank detection...")
    from memory_bank_core.utils.session_parser import detect_memory_bank_sessions
    
    memory_bank_sessions = detect_memory_bank_sessions(project_path)
    print(f"Detected {len(memory_bank_sessions)} memory bank sessions")
    
    if memory_bank_sessions:
        print("\nTop memory bank sessions:")
        for i, session in enumerate(memory_bank_sessions[:5], 1):
            print(f"{i}. {session['session_id']}: {session['total_tokens']:,} tokens, ${session['estimated_cost']:.4f}")
    
    return len(memory_bank_sessions)


if __name__ == "__main__":
    debug_session_detection()