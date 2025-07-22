"""
Test Complete Multi-Agent System: All 3 Phases
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add paths to import our modules
sys.path.append(str(Path(__file__).parent))

from memory_bank_core.builders.multi_agent_builder import MultiAgentMemoryBankBuilder
from memory_bank_core.models.build_job import BuildConfig, BuildMode


async def test_complete_multi_agent_system():
    """Test all 3 phases of the multi-agent system"""
    
    # Use the pc_cortex repo itself as test case
    repo_path = Path(__file__).parent
    output_path = Path(__file__).parent / "test_output" / f"full_multi_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Testing Complete Multi-Agent System on: {repo_path}")
    print(f"📁 Output will be saved to: {output_path}")
    print("=" * 80)
    
    # Progress callback with timestamp and phase tracking
    def progress_callback(message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        # Color-code phases
        if "PHASE 1" in message:
            print(f"[{timestamp}] 🏗️  {message}")
        elif "PHASE 2" in message:
            print(f"[{timestamp}] 🔨 {message}")  
        elif "PHASE 3" in message:
            print(f"[{timestamp}] 🔍 {message}")
        else:
            print(f"[{timestamp}] {message}")
    
    # Create builder and config
    builder = MultiAgentMemoryBankBuilder(repo_path.parent)
    
    config = BuildConfig(
        repo_path=str(repo_path),
        output_path=str(output_path),
        mode=BuildMode.MULTI_AGENT,
        max_turns=200  # 200 for arch, 100 per component, 50 per validator
    )
    
    try:
        print("\n🚀 Starting Complete Multi-Agent Analysis (3 Phases)")
        print("📋 Configuration:")
        print(f"   • Architecture Analysis: max 200 turns")
        print(f"   • Component Analysis: max 100 turns per component (up to 15 concurrent)")
        print(f"   • Validation & Auto-Fix: max 50 turns per validator (up to 10 concurrent)")
        print("-" * 80)
        
        start_time = datetime.now()
        
        result = await builder.build_memory_bank(
            config=config,
            progress_callback=progress_callback
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 COMPLETE MULTI-AGENT RESULTS:")
        print("=" * 80)
        
        if result.success:
            print("✅ Multi-agent analysis completed successfully!")
            print(f"⏱️  Total Duration: {duration:.2f} seconds")
            
            print(f"\n📁 Total Files Created: {len(result.files_written)}")
            
            print(f"\n📈 Phase Summary:")
            metadata = result.metadata
            
            # Phase 1 Summary
            print(f"  🏗️  Phase 1 (Architecture):")
            print(f"      • System Type: {metadata.get('architecture_type', 'Unknown')}")
            print(f"      • Components Identified: {metadata.get('total_components', 0)}")
            print(f"      • Status: {'✅ Complete' if metadata.get('phase_1_complete') else '❌ Failed'}")
            
            # Phase 2 Summary  
            print(f"  🔨 Phase 2 (Components):")
            if metadata.get('phase_2_complete'):
                successful = metadata.get('successful_components', 0)
                failed = metadata.get('failed_components', 0) 
                duration_2 = metadata.get('component_analysis_duration', 0)
                print(f"      • Successful: {successful}, Failed: {failed}")
                print(f"      • Duration: {duration_2:.2f}s")
                print(f"      • Status: {'✅ Complete' if successful > 0 else '⚠️ No Success'}")
            else:
                print(f"      • Status: ⏭️ Skipped")
            
            # Phase 3 Summary
            print(f"  🔍 Phase 3 (Validation):")
            if metadata.get('phase_3_complete'):
                passed = metadata.get('validation_passed', 0)
                failed = metadata.get('validation_failed', 0)
                partial = metadata.get('validation_partial', 0)
                issues_found = metadata.get('total_issues_found', 0)
                issues_fixed = metadata.get('total_issues_fixed', 0)
                fix_rate = metadata.get('fix_success_rate', 0)
                validation_duration = metadata.get('validation_duration', 0)
                
                print(f"      • Passed: {passed}, Partial: {partial}, Failed: {failed}")
                print(f"      • Issues Found: {issues_found}, Fixed: {issues_fixed}")
                print(f"      • Fix Success Rate: {fix_rate:.1%}")
                print(f"      • Duration: {validation_duration:.2f}s")
                print(f"      • Status: ✅ Complete")
            else:
                print(f"      • Status: ⏭️ Skipped")
            
            # Show final structure
            print(f"\n📂 Generated Structure:")
            print("-" * 80)
            _show_directory_structure(output_path)
            
            # Show summary files content
            _show_summary_files(output_path)
            
        else:
            print("❌ Multi-agent analysis failed!")
            print(f"Errors: {result.errors}")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Complete Multi-Agent Test finished!")


def _show_directory_structure(output_path: Path, max_depth: int = 3):
    """Show the directory structure up to max_depth"""
    
    def _print_tree(path: Path, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
            
        if path.is_dir():
            print(f"{prefix}📁 {path.name}/")
            if depth < max_depth:
                children = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                for i, child in enumerate(children):
                    is_last = i == len(children) - 1
                    child_prefix = prefix + ("└── " if is_last else "├── ")
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    
                    if child.is_file():
                        size = child.stat().st_size
                        size_str = f" ({size} bytes)" if size < 10000 else f" ({size//1000}KB)"
                        print(f"{child_prefix}📄 {child.name}{size_str}")
                    else:
                        print(f"{child_prefix}📁 {child.name}/")
                        if depth + 1 < max_depth:
                            _print_tree(child, next_prefix, depth + 1)
        else:
            size = path.stat().st_size if path.exists() else 0
            size_str = f" ({size} bytes)" if size < 10000 else f" ({size//1000}KB)"
            print(f"{prefix}📄 {path.name}{size_str}")
    
    _print_tree(output_path)


def _show_summary_files(output_path: Path):
    """Show content of key summary files"""
    
    summary_files = [
        ("architecture_manifest.json", "🏗️ Architecture Summary"),
        ("component_analysis_summary.json", "🔨 Component Analysis Summary"),  
        ("validation_summary.json", "🔍 Validation Summary")
    ]
    
    for filename, title in summary_files:
        file_path = output_path / filename
        if file_path.exists():
            print(f"\n{title}:")
            print("-" * 40)
            try:
                import json
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if filename == "architecture_manifest.json":
                    print(f"System Type: {data.get('system_type', 'Unknown')}")
                    print(f"Total Components: {data.get('total_components', 0)}")
                    components = data.get('components', [])
                    if components:
                        print("Components:")
                        for comp in components[:5]:  # Show first 5
                            print(f"  • {comp.get('name', 'Unknown')} ({comp.get('type', 'Unknown')})")
                        if len(components) > 5:
                            print(f"  ... and {len(components) - 5} more")
                            
                elif filename == "component_analysis_summary.json":
                    print(f"Success Rate: {data.get('success_rate', 0):.1%}")
                    print(f"Duration: {data.get('total_duration_seconds', 0):.2f}s")
                    print(f"Successful: {data.get('successful_components', 0)}")
                    print(f"Failed: {data.get('failed_components', 0)}")
                    
                elif filename == "validation_summary.json":
                    print(f"Pass Rate: {data.get('pass_rate', 0):.1%}")
                    print(f"Issues Found: {data.get('total_issues_found', 0)}")
                    print(f"Issues Fixed: {data.get('total_issues_fixed', 0)}")
                    print(f"Fix Success Rate: {data.get('fix_success_rate', 0):.1%}")
                    
            except Exception as e:
                print(f"Error reading {filename}: {e}")


if __name__ == "__main__":
    print("🧪 Complete Multi-Agent System Test (3 Phases)")
    print("=" * 80)
    
    # Run the test
    asyncio.run(test_complete_multi_agent_system())