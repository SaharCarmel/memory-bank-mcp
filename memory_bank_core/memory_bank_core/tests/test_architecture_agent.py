"""
Test script for Architecture Agent - Phase 1 testing
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.agents.architecture_agent import ArchitectureAgent
from core.builders.multi_agent_builder import MultiAgentMemoryBankBuilder
from core.models.build_job import BuildConfig, BuildMode


async def test_architecture_agent():
    """Test the Architecture Agent on the current repository"""
    
    # Use the pc_cortex repo itself as a test case
    repo_path = Path(__file__).parent.parent.parent  # pc_cortex root
    output_path = repo_path / "test_output" / f"architecture_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"Testing Architecture Agent on: {repo_path}")
    print(f"Output will be saved to: {output_path}")
    print("-" * 80)
    
    # Progress callback to see what's happening
    def progress_callback(message: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    # Test using the multi-agent builder
    builder = MultiAgentMemoryBankBuilder(repo_path)
    
    config = BuildConfig(
        repo_path=str(repo_path),
        output_path=str(output_path),
        mode=BuildMode.MULTI_AGENT,
        max_turns=100
    )
    
    try:
        result = await builder.build_memory_bank(
            config=config,
            progress_callback=progress_callback
        )
        
        print("\n" + "=" * 80)
        print("PHASE 1 RESULTS:")
        print("=" * 80)
        
        if result.success:
            print("✓ Architecture analysis completed successfully!")
            print(f"\nFiles created:")
            for file in result.files_written:
                print(f"  - {file}")
            
            print(f"\nMetadata:")
            for key, value in result.metadata.items():
                print(f"  - {key}: {value}")
            
            # Read and display the manifest
            manifest_path = Path(output_path) / "architecture_manifest.md"
            if manifest_path.exists():
                print(f"\n{'-' * 80}")
                print("ARCHITECTURE MANIFEST PREVIEW:")
                print('-' * 80)
                with open(manifest_path, 'r') as f:
                    content = f.read()
                    # Show first 1000 characters
                    print(content[:1000])
                    if len(content) > 1000:
                        print("\n... (truncated)")
        else:
            print("✗ Architecture analysis failed!")
            print(f"Errors: {result.errors}")
            
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_direct_architecture_agent():
    """Test the Architecture Agent directly (without builder wrapper)"""
    
    print("\n" + "=" * 80)
    print("DIRECT ARCHITECTURE AGENT TEST")
    print("=" * 80)
    
    # Use a simpler test repo if available
    test_repo = Path(__file__).parent.parent.parent  # pc_cortex itself
    output_path = test_repo / "test_output" / "direct_test"
    output_path.mkdir(parents=True, exist_ok=True)
    
    agent = ArchitectureAgent(test_repo)
    
    def progress_callback(message: str):
        print(f"[DIRECT] {message}")
    
    try:
        manifest = await agent.analyze(
            repo_path=str(test_repo),
            output_path=str(output_path),
            progress_callback=progress_callback
        )
        
        print(f"\nDirect test results:")
        print(f"  System Type: {manifest.system_type}")
        print(f"  Total Components: {manifest.total_components}")
        print(f"  Components: {[c.name for c in manifest.components]}")
        
    except Exception as e:
        print(f"Direct test failed: {e}")


if __name__ == "__main__":
    print("Starting Architecture Agent Phase 1 Testing")
    print("=" * 80)
    
    # Run the test
    asyncio.run(test_architecture_agent())
    
    # Optionally run direct test
    # asyncio.run(test_direct_architecture_agent())