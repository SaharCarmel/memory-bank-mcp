#!/usr/bin/env python3
"""
Test Cost Integration with Multi-Agent Memory Bank Builder

This script tests the integrated cost tracking functionality
"""

import asyncio
import sys
from pathlib import Path

# Add path for imports
sys.path.append(str(Path(__file__).parent))

from memory_bank_core.builders.multi_agent_builder import MultiAgentMemoryBankBuilder
from memory_bank_core.models.build_job import BuildConfig
from memory_bank_core.utils.cost_calculator import CostCalculator, ClaudeModel
from memory_bank_core.utils.session_parser import detect_memory_bank_sessions


async def test_cost_integration():
    """Test the cost tracking integration in the multi-agent builder"""
    
    print("🧪 Testing Cost Integration with Multi-Agent Builder")
    print("=" * 60)
    
    # Setup test paths
    repo_path = Path(__file__).parent / "demo_repo"
    output_path = Path(__file__).parent / "test_cost_integration_output"
    
    if not repo_path.exists():
        print(f"❌ Test repo not found: {repo_path}")
        return
    
    # Initialize builder with cost tracking enabled
    builder = MultiAgentMemoryBankBuilder(
        root_path=Path(__file__).parent,
        enable_cost_tracking=True
    )
    
    print(f"✅ Multi-agent builder initialized with cost tracking")
    print(f"📂 Repo path: {repo_path}")
    print(f"📁 Output path: {output_path}")
    print(f"💰 Cost calculator model: {builder.cost_calculator.model.value}")
    
    # Create build config
    config = BuildConfig(
        repo_path=str(repo_path),
        output_path=str(output_path),
        max_turns=100  # Reduced for testing
    )
    
    # Track progress and cost messages
    progress_messages = []
    cost_messages = []
    
    def progress_callback(message: str):
        """Capture progress messages"""
        progress_messages.append(message)
        print(f"📝 {message}")
        
        # Track cost-related messages
        if any(keyword in message.lower() for keyword in ['cost', '$', 'tokens']):
            cost_messages.append(message)
    
    print("\n🚀 Starting multi-agent build with cost tracking...")
    print("-" * 60)
    
    # Run the build
    result = await builder.build_memory_bank(config, progress_callback)
    
    print("\n" + "=" * 60)
    print("🔍 BUILD RESULTS")
    print("=" * 60)
    
    print(f"✅ Build Success: {result.success}")
    print(f"📁 Output Path: {result.output_path}")
    print(f"📄 Files Written: {len(result.files_written)}")
    
    if result.errors:
        print(f"❌ Errors: {result.errors}")
    
    # Check for cost tracking in metadata
    if "cost_tracking" in result.metadata:
        cost_data = result.metadata["cost_tracking"]
        print("\n💰 COST TRACKING RESULTS")
        print("-" * 60)
        print(f"Tracking Enabled: {cost_data['enabled']}")
        print(f"Total Cost: ${cost_data['total_cost']:.4f}")
        print(f"Input Tokens: {cost_data['input_tokens']:,}")
        print(f"Output Tokens: {cost_data['output_tokens']:,}")
        print(f"Total Tokens: {cost_data['total_tokens']:,}")
        print(f"Model Used: {cost_data['model_used']}")
        
        if cost_data.get('phase_costs'):
            print("\n📊 Phase Cost Breakdown:")
            for phase, cost in cost_data['phase_costs'].items():
                print(f"  {phase}: ${cost:.4f}")
        
        if cost_data.get('component_costs'):
            print("\n🧩 Component Cost Breakdown:")
            for component, cost in cost_data['component_costs'].items():
                print(f"  {component}: ${cost:.4f}")
    else:
        print("\n⚠️  No cost tracking data found in build metadata")
    
    # Show cost-related progress messages
    if cost_messages:
        print("\n💬 Cost-Related Messages:")
        print("-" * 60)
        for msg in cost_messages:
            print(f"  {msg}")
    
    # Analyze project sessions for comparison
    print("\n🔍 Analyzing Recent Memory Bank Sessions...")
    print("-" * 60)
    
    project_sessions = detect_memory_bank_sessions(str(Path(__file__).parent))
    
    if project_sessions:
        print(f"Found {len(project_sessions)} recent memory bank sessions:")
        for i, session in enumerate(project_sessions[:3], 1):  # Show top 3
            print(f"{i}. Session {session['session_id']}: "
                  f"{session['total_tokens']:,} tokens, "
                  f"${session['estimated_cost']:.4f}")
    else:
        print("No recent memory bank sessions detected")
    
    # Cost calculator demonstration
    print("\n💡 Cost Estimation Demonstration")
    print("-" * 60)
    
    calculator = CostCalculator(ClaudeModel.CLAUDE_4_SONNET)
    
    # Estimate cost for different project sizes
    estimates = [
        ("Small (5 components)", calculator.estimate_cost(num_components=5)),
        ("Medium (15 components)", calculator.estimate_cost(num_components=15)),
        ("Large (25 components)", calculator.estimate_cost(num_components=25))
    ]
    
    for name, estimate in estimates:
        print(f"{name}: ${estimate['total_estimated_cost']:.2f}")
    
    print("\n" + "=" * 60)
    print("🎉 Cost integration test complete!")
    
    return result


async def main():
    """Main test function"""
    try:
        result = await test_cost_integration()
        print(f"\n✅ Test completed successfully: {result.success}")
        return 0 if result.success else 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)