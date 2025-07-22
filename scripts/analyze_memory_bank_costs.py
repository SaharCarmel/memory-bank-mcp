"""
Memory Bank Cost Analyzer

Analyzes Claude Code session logs to calculate costs for memory bank building operations.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add paths to import our modules
sys.path.append(str(Path(__file__).parent))

from memory_bank_core.utils.session_parser import SessionParser, detect_memory_bank_sessions
from memory_bank_core.utils.cost_calculator import CostCalculator, ClaudeModel


def analyze_project_costs(project_path: str = None):
    """Analyze costs for memory bank building in this project"""
    
    if not project_path:
        project_path = str(Path(__file__).parent.absolute())
    
    parser = SessionParser()
    
    print("🔍 Memory Bank Cost Analysis")
    print("=" * 60)
    print(f"Project Path: {project_path}")
    
    # Find recent memory bank building sessions
    print("\n📊 Detecting Memory Bank Building Sessions...")
    memory_bank_sessions = detect_memory_bank_sessions(project_path)
    
    if not memory_bank_sessions:
        print("No memory bank building sessions detected.")
        return
    
    print(f"Found {len(memory_bank_sessions)} potential memory bank sessions:")
    print("-" * 60)
    
    total_cost = 0
    total_tokens = 0
    
    for i, session in enumerate(memory_bank_sessions[:10], 1):  # Show top 10
        print(f"{i:2d}. Session {session['session_id']}")
        print(f"    📅 Date: {session['start_time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"    ⏱️  Duration: {session['duration_hours']:.1f} hours")
        print(f"    🏷️  Model: {session['model']}")
        print(f"    📝 Messages: {session['messages']}")
        print(f"    🔢 Tokens: {session['total_tokens']:,}")
        print(f"    💰 Cost: ${session['estimated_cost']:.4f}")
        
        if session['likely_memory_bank_session']:
            print(f"    🤖 Likely Multi-Agent Session")
        
        total_cost += session['estimated_cost']
        total_tokens += session['total_tokens']
        print()
    
    print("=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)
    print(f"Total Sessions Analyzed: {len(memory_bank_sessions)}")
    print(f"Total Tokens Used: {total_tokens:,}")
    print(f"Total Estimated Cost: ${total_cost:.4f}")
    print(f"Average Cost per Session: ${total_cost/len(memory_bank_sessions):.4f}")
    
    # Analyze recent usage (last 24 hours)
    print("\n📊 Recent Usage Analysis (Last 24 Hours)")
    print("-" * 60)
    
    recent_analysis = parser.analyze_recent_usage(
        project_path=project_path,
        hours=24,
        model=ClaudeModel.CLAUDE_4_SONNET
    )
    
    if recent_analysis["sessions"] > 0:
        print(f"Sessions in Last 24h: {recent_analysis['sessions']}")
        print(f"Total Messages: {recent_analysis['total_messages']}")
        print(f"Total Duration: {recent_analysis['total_duration_hours']:.1f} hours")
        print(f"Total Tokens: {recent_analysis['total_tokens']:,}")
        print(f"Total Cost: ${recent_analysis['total_cost']:.4f}")
        print(f"Average per Session: ${recent_analysis['average_cost_per_session']:.4f}")
        print(f"Model Used: {recent_analysis['model_used']}")
    else:
        print("No sessions found in the last 24 hours.")
    
    # Cost projections for multi-agent builds
    print("\n💡 Multi-Agent Build Cost Projections")
    print("-" * 60)
    
    calculator = CostCalculator(ClaudeModel.CLAUDE_4_SONNET)
    
    # Small project (5 components)
    small_estimate = calculator.estimate_cost(
        num_components=5,
        avg_turns_architecture=150,
        avg_turns_per_component=75,
        avg_turns_per_validation=50
    )
    
    # Medium project (15 components) 
    medium_estimate = calculator.estimate_cost(
        num_components=15,
        avg_turns_architecture=200,
        avg_turns_per_component=100,
        avg_turns_per_validation=50
    )
    
    # Large project (25 components)
    large_estimate = calculator.estimate_cost(
        num_components=25,
        avg_turns_architecture=200,
        avg_turns_per_component=100,
        avg_turns_per_validation=75
    )
    
    print("Estimated Costs by Project Size (Claude 4 Sonnet):")
    print(f"  Small (5 components):  ${small_estimate['total_estimated_cost']:.2f}")
    print(f"  Medium (15 components): ${medium_estimate['total_estimated_cost']:.2f}")
    print(f"  Large (25 components):  ${large_estimate['total_estimated_cost']:.2f}")
    
    print("\nCost Range Estimates (±30-50% variance):")
    print(f"  Small:  ${small_estimate['cost_range']['low']:.2f} - ${small_estimate['cost_range']['high']:.2f}")
    print(f"  Medium: ${medium_estimate['cost_range']['low']:.2f} - ${medium_estimate['cost_range']['high']:.2f}")
    print(f"  Large:  ${large_estimate['cost_range']['low']:.2f} - ${large_estimate['cost_range']['high']:.2f}")
    
    # Cost by model comparison
    print("\n🏷️  Model Cost Comparison (Medium Project, 15 components)")
    print("-" * 60)
    
    models_to_compare = [
        (ClaudeModel.CLAUDE_3_HAIKU, "Claude 3 Haiku (Cheapest)"),
        (ClaudeModel.CLAUDE_35_HAIKU, "Claude 3.5 Haiku (Fast)"),
        (ClaudeModel.CLAUDE_35_SONNET, "Claude 3.5 Sonnet (Balanced)"),
        (ClaudeModel.CLAUDE_4_SONNET, "Claude 4 Sonnet (Current)"),
        (ClaudeModel.CLAUDE_4_OPUS, "Claude 4 Opus (Most Advanced)")
    ]
    
    for model, description in models_to_compare:
        calc = CostCalculator(model)
        estimate = calc.estimate_cost(num_components=15)
        print(f"{description:25}: ${estimate['total_estimated_cost']:7.2f}")
    
    # Save detailed report
    save_report = input("\n💾 Save detailed cost report to file? (y/n): ").lower().strip() == 'y'
    if save_report:
        output_dir = Path(__file__).parent / "cost_reports"
        output_dir.mkdir(exist_ok=True)
        
        report_file = output_dir / f"memory_bank_cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "analysis_date": datetime.now().isoformat(),
            "project_path": project_path,
            "memory_bank_sessions": memory_bank_sessions,
            "recent_usage": recent_analysis,
            "cost_estimates": {
                "small_project": small_estimate,
                "medium_project": medium_estimate,  
                "large_project": large_estimate
            },
            "model_comparison": {
                model.value: CostCalculator(model).estimate_cost(num_components=15)
                for model, _ in models_to_compare
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"📄 Detailed report saved to: {report_file}")
    
    print("\n" + "=" * 60)
    print("Cost analysis complete!")


def analyze_specific_session(session_id: str, project_path: str = None):
    """Analyze a specific session by ID"""
    if not project_path:
        project_path = str(Path(__file__).parent.absolute())
    
    parser = SessionParser()
    sessions = parser.get_project_token_usage(project_path)
    
    # Find matching session
    target_session = None
    for session in sessions:
        if session.session_id.startswith(session_id):
            target_session = session
            break
    
    if not target_session:
        print(f"❌ Session {session_id} not found")
        return
    
    print(f"🔍 Analyzing Session: {target_session.session_id}")
    print("=" * 60)
    print(f"Start Time: {target_session.session_start}")
    print(f"End Time: {target_session.session_end}")
    print(f"Duration: {(target_session.session_end - target_session.session_start).total_seconds() / 3600:.2f} hours")
    print(f"Working Directory: {target_session.working_directory}")
    print(f"Model: {target_session.model_used}")
    print(f"Messages: {target_session.message_count}")
    print()
    print("Token Usage:")
    print(f"  Input Tokens: {target_session.total_input_tokens:,}")
    print(f"  Output Tokens: {target_session.total_output_tokens:,}")
    print(f"  Cache Creation: {target_session.cache_creation_tokens:,}")
    print(f"  Cache Read: {target_session.cache_read_tokens:,}")
    print(f"  Total Billable: {target_session.total_input_tokens + target_session.cache_creation_tokens + target_session.total_output_tokens:,}")
    
    # Calculate cost
    calculator = CostCalculator(ClaudeModel.CLAUDE_4_SONNET)
    calculator.add_token_usage(
        target_session.total_input_tokens + target_session.cache_creation_tokens,
        target_session.total_output_tokens,
        f"session_{target_session.session_id[:8]}"
    )
    
    cost = calculator.calculate_cost()
    print()
    print("Cost Analysis:")
    print(f"  Input Cost: ${cost.input_cost:.4f}")
    print(f"  Output Cost: ${cost.output_cost:.4f}")
    print(f"  Total Cost: ${cost.total_cost:.4f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--session":
        if len(sys.argv) < 3:
            print("Usage: python analyze_memory_bank_costs.py --session <session_id>")
            sys.exit(1)
        project_path = sys.argv[3] if len(sys.argv) > 3 else None
        analyze_specific_session(sys.argv[2], project_path)
    else:
        # Check if project path is provided as argument
        project_path = sys.argv[1] if len(sys.argv) > 1 else None
        analyze_project_costs(project_path)