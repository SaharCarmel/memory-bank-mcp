#!/usr/bin/env python3
"""
Get the cost for a specific memory bank build based on timestamp
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add path for imports
sys.path.append(str(Path(__file__).parent))

from memory_bank_core.utils.session_parser import SessionParser, detect_memory_bank_sessions
from memory_bank_core.utils.cost_calculator import CostCalculator, ClaudeModel


def get_build_cost_for_output(output_dir: str):
    """
    Analyze the cost for the build that created a specific output directory
    
    Args:
        output_dir: Path to the build output directory (e.g., test_output/full_multi_agent_20250723_014644/)
    """
    
    # Parse timestamp from directory name
    # Format: full_multi_agent_YYYYMMDD_HHMMSS
    dir_name = Path(output_dir).name
    if 'full_multi_agent_' in dir_name:
        timestamp_str = dir_name.split('full_multi_agent_')[1]  # 20250723_014644
        try:
            # Parse the timestamp
            build_datetime = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            build_datetime = build_datetime.replace(tzinfo=timezone.utc)
            
            print(f"🔍 Analyzing cost for build at: {build_datetime}")
            print(f"📁 Output directory: {output_dir}")
            print("=" * 60)
            
            # Look for sessions within a 2-hour window around the build time
            start_time = build_datetime - timedelta(hours=1)
            end_time = build_datetime + timedelta(hours=1)
            
            print(f"🕒 Time window: {start_time} to {end_time}")
            
            # Get sessions for the project
            project_path = "/Users/saharcarmel/Code/personal/future/pc_cortex"
            parser = SessionParser()
            
            # Get sessions in the time window
            calculator, sessions = parser.calculate_project_cost(
                project_path=project_path,
                model=ClaudeModel.CLAUDE_4_SONNET,
                time_filter=(start_time, end_time)
            )
            
            if sessions:
                print(f"\n📊 Found {len(sessions)} session(s) in the build window:")
                print("-" * 60)
                
                total_tokens = 0
                total_messages = 0
                
                for session in sessions:
                    tokens = session.total_input_tokens + session.total_output_tokens
                    total_tokens += tokens
                    total_messages += session.message_count
                    
                    print(f"Session {session.session_id[:8]}:")
                    print(f"  📅 Start: {session.session_start}")
                    print(f"  📅 End: {session.session_end}")
                    print(f"  🔢 Tokens: {tokens:,}")
                    print(f"  📝 Messages: {session.message_count}")
                    print(f"  🏷️  Model: {session.model_used}")
                    print()
                
                # Calculate cost
                cost_breakdown = calculator.calculate_cost()
                
                print("💰 BUILD COST SUMMARY")
                print("=" * 60)
                print(f"Total Input Tokens: {cost_breakdown.total_input_tokens:,}")
                print(f"Total Output Tokens: {cost_breakdown.total_output_tokens:,}")
                print(f"Total Tokens: {cost_breakdown.total_tokens:,}")
                print(f"Total Messages: {total_messages}")
                print(f"TOTAL COST: ${cost_breakdown.total_cost:.4f}")
                
                if cost_breakdown.phase_costs:
                    print(f"\n📊 Phase Breakdown:")
                    for phase, cost in cost_breakdown.phase_costs.items():
                        print(f"  {phase}: ${cost:.4f}")
                
                return cost_breakdown.total_cost
                
            else:
                print("❌ No sessions found in the build time window")
                
                # Show nearby sessions for reference
                print(f"\n🔍 Looking for sessions within 6 hours...")
                nearby_start = build_datetime - timedelta(hours=6)
                nearby_end = build_datetime + timedelta(hours=6)
                
                nearby_calculator, nearby_sessions = parser.calculate_project_cost(
                    project_path=project_path,
                    model=ClaudeModel.CLAUDE_4_SONNET,
                    time_filter=(nearby_start, nearby_end)
                )
                
                if nearby_sessions:
                    print(f"Found {len(nearby_sessions)} nearby session(s):")
                    for session in nearby_sessions:
                        print(f"  {session.session_id[:8]}: {session.session_start} ({session.total_input_tokens + session.total_output_tokens:,} tokens)")
                else:
                    print("No nearby sessions found either")
                
                return 0
                
        except ValueError as e:
            print(f"❌ Could not parse timestamp from directory name: {e}")
            return None
    else:
        print(f"❌ Directory name doesn't match expected format: {dir_name}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python get_build_cost.py <output_directory>")
        print("Example: python get_build_cost.py test_output/full_multi_agent_20250723_014644/")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    if not Path(output_dir).exists():
        print(f"❌ Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    cost = get_build_cost_for_output(output_dir)
    
    if cost is not None:
        print(f"\n🎉 Analysis complete! Build cost: ${cost:.4f}")
    else:
        print(f"\n❌ Could not determine build cost")
        sys.exit(1)


if __name__ == "__main__":
    main()