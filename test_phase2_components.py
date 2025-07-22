"""
Test Phase 2: Component Agents & Orchestration
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add paths to import our modules
sys.path.append(str(Path(__file__).parent))

from memory_bank_core.builders.multi_agent_builder import MultiAgentMemoryBankBuilder
from memory_bank_core.models.build_job import BuildConfig, BuildMode


async def test_phase2_with_small_repo():
    """Test Phase 2 with a smaller repository first"""
    
    # Use the pc_cortex repo itself as test case
    repo_path = Path(__file__).parent
    output_path = Path(__file__).parent / "test_output" / f"phase2_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Testing Phase 1 + Phase 2 on: {repo_path}")
    print(f"📁 Output will be saved to: {output_path}")
    print("=" * 80)
    
    # Progress callback with timestamp
    def progress_callback(message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    # Create builder and config
    builder = MultiAgentMemoryBankBuilder(repo_path.parent)
    
    config = BuildConfig(
        repo_path=str(repo_path),
        output_path=str(output_path),
        mode=BuildMode.MULTI_AGENT,
        max_turns=150  # Reasonable for testing
    )
    
    try:
        print("\n🚀 Starting Multi-Agent Analysis (Phase 1 + 2)")
        print("ℹ️  Architecture Analysis: max 150 turns")
        print("ℹ️  Component Analysis: max 75 turns per component")
        print("-" * 80)
        
        start_time = datetime.now()
        
        result = await builder.build_memory_bank(
            config=config,
            progress_callback=progress_callback
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 PHASE 2 TEST RESULTS:")
        print("=" * 80)
        
        if result.success:
            print("✅ Multi-agent analysis completed successfully!")
            print(f"⏱️  Total Duration: {duration:.2f} seconds")
            
            print(f"\n📁 Files created: {len(result.files_written)}")
            
            print(f"\n📈 Metadata:")
            for key, value in result.metadata.items():
                if key == "components":
                    print(f"  - {key}: {len(value)} components")
                    for comp in value:
                        print(f"    • {comp}")
                elif key in ["successful_components", "failed_components"]:
                    print(f"  - {key}: {value}")
                elif key == "component_analysis_duration":
                    print(f"  - {key}: {value:.2f}s")
                else:
                    print(f"  - {key}: {value}")
            
            # Show component structure
            components_dir = output_path / "components"
            if components_dir.exists():
                print(f"\n📂 Component Memory Banks:")
                print("-" * 80)
                for comp_dir in components_dir.iterdir():
                    if comp_dir.is_dir():
                        memory_bank_dir = comp_dir / "memory-bank"
                        if memory_bank_dir.exists():
                            files = list(memory_bank_dir.glob("*.md"))
                            print(f"  📁 {comp_dir.name}:")
                            for file in files:
                                size = file.stat().st_size
                                print(f"    - {file.name} ({size} bytes)")
            
            # Check orchestration summary
            summary_path = output_path / "component_analysis_summary.json"
            if summary_path.exists():
                import json
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                    print(f"\n📊 Component Analysis Summary:")
                    print(f"  - Success Rate: {summary['success_rate']:.1%}")
                    print(f"  - Duration: {summary['total_duration_seconds']:.2f}s")
                    print(f"  - Max Concurrent Agents: {summary['orchestration_metadata']['max_concurrent_agents']}")
                    
                    if summary['component_summaries']:
                        print(f"  - Component Details:")
                        for comp in summary['component_summaries']:
                            status = "✅" if comp['success'] else "❌"
                            print(f"    {status} {comp['component_name']}: {comp['files_created']} files, {comp['turn_count']} turns")
            
        else:
            print("❌ Multi-agent analysis failed!")
            print(f"Errors: {result.errors}")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Phase 2 Test completed!")


if __name__ == "__main__":
    print("🧪 Phase 2: Component Analysis Test")
    print("=" * 80)
    
    # Run the test
    asyncio.run(test_phase2_with_small_repo())