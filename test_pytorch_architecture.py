"""
Test Architecture Agent on PyTorch repository
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add paths to import our modules
sys.path.append(str(Path(__file__).parent))

from memory_bank_core.agents.architecture_agent import ArchitectureAgent
from memory_bank_core.builders.multi_agent_builder import MultiAgentMemoryBankBuilder
from memory_bank_core.models.build_job import BuildConfig, BuildMode


async def test_pytorch_architecture():
    """Test the Architecture Agent on PyTorch repository"""
    
    # Path to PyTorch repository
    pytorch_path = Path(__file__).parent / "pytorch"
    
    if not pytorch_path.exists():
        print(f"❌ PyTorch repository not found at: {pytorch_path}")
        print("Please run: git clone git@github.com:pytorch/pytorch.git")
        return
    
    # Create output directory
    output_path = Path(__file__).parent / "test_output" / f"pytorch_architecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Analyzing PyTorch repository at: {pytorch_path}")
    print(f"📁 Output will be saved to: {output_path}")
    print("=" * 80)
    
    # Progress callback with timestamp
    def progress_callback(message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    # Create builder and config
    builder = MultiAgentMemoryBankBuilder(pytorch_path.parent)
    
    config = BuildConfig(
        repo_path=str(pytorch_path),
        output_path=str(output_path),
        mode=BuildMode.MULTI_AGENT,
        max_turns=200  # Ensure this is passed through
    )
    
    try:
        print("\n🚀 Starting Architecture Analysis (Phase 1)")
        print("ℹ️  Max turns: 200 (warning at 190)")
        print("-" * 80)
        
        start_time = datetime.now()
        
        result = await builder.build_memory_bank(
            config=config,
            progress_callback=progress_callback
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 ANALYSIS RESULTS:")
        print("=" * 80)
        
        if result.success:
            print("✅ Architecture analysis completed successfully!")
            print(f"⏱️  Duration: {duration:.2f} seconds")
            print(f"\n📁 Files created:")
            for file in result.files_written:
                print(f"  - {file}")
            
            print(f"\n📈 Metadata:")
            for key, value in result.metadata.items():
                if key == "components":
                    print(f"  - {key}: {len(value)} components")
                    for comp in value[:5]:  # Show first 5 components
                        print(f"    • {comp}")
                    if len(value) > 5:
                        print(f"    ... and {len(value) - 5} more")
                else:
                    print(f"  - {key}: {value}")
            
            # Read and display part of the manifest
            manifest_path = output_path / "architecture_manifest.md"
            if manifest_path.exists():
                print(f"\n📄 Architecture Manifest Preview:")
                print("-" * 80)
                with open(manifest_path, 'r') as f:
                    content = f.read()
                    # Show first 2000 characters
                    preview = content[:2000]
                    print(preview)
                    if len(content) > 2000:
                        print(f"\n... (showing first 2000 of {len(content)} characters)")
                    
                    # Count components in manifest
                    component_count = content.count("### Component:")
                    print(f"\n📊 Total components identified: {component_count}")
            
            # Check JSON manifest
            json_manifest_path = output_path / "architecture_manifest.json"
            if json_manifest_path.exists():
                import json
                with open(json_manifest_path, 'r') as f:
                    json_data = json.load(f)
                    print(f"\n🔧 System Type: {json_data.get('system_type', 'Unknown')}")
                    print(f"📦 Total Components: {json_data.get('total_components', 0)}")
                    
        else:
            print("❌ Architecture analysis failed!")
            print(f"Errors: {result.errors}")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Test completed!")


if __name__ == "__main__":
    print("🧪 PyTorch Architecture Analysis Test")
    print("=" * 80)
    
    # Run the test
    asyncio.run(test_pytorch_architecture())