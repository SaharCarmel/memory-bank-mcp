#!/usr/bin/env python3
"""
Test script for the new backend-integrated memory bank builder
"""

import asyncio
import sys
from pathlib import Path
from app.services.memory_bank_builder import MemoryBankBuilder
from app.services.claude_integration import ClaudeIntegrationService

async def test_claude_connection():
    """Test Claude Code SDK connection"""
    print("Testing Claude Code SDK connection...")
    try:
        service = ClaudeIntegrationService()
        result = await service.test_connection()
        if result:
            print("✅ Claude Code SDK connection successful")
            return True
        else:
            print("❌ Claude Code SDK connection failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_memory_bank_build():
    """Test memory bank building"""
    print("\nTesting memory bank builder...")
    
    # Use the demo_repo for testing if it exists
    root_path = Path(__file__).parent.parent
    test_repo = root_path / "demo_repo"
    
    if not test_repo.exists():
        print(f"⚠️  Test repository not found at {test_repo}")
        print("Creating a minimal test repo...")
        test_repo.mkdir(exist_ok=True)
        (test_repo / "README.md").write_text("# Test Repository\nThis is a test repository for memory bank building.")
        (test_repo / "main.py").write_text('print("Hello, World!")')
    
    try:
        builder = MemoryBankBuilder(root_path)
        
        async def progress_callback(message: str):
            print(f"  📝 {message}")
        
        print(f"Building memory bank for: {test_repo}")
        result = await builder.build_memory_bank(
            repo_path=str(test_repo),
            output_name="test_memory_bank",
            progress_callback=progress_callback
        )
        
        print(f"\n✅ Memory bank built successfully!")
        print(f"   Output path: {result['output_path']}")
        print(f"   Files written: {len(result['files_written'])}")
        print(f"   Mode: {result['mode']}")
        return True
        
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=== Backend Integration Test Suite ===\n")
    
    # Test 1: Claude connection
    claude_ok = await test_claude_connection()
    
    if not claude_ok:
        print("\n⚠️  Claude Code SDK is not properly configured.")
        print("Make sure you have:")
        print("1. Installed claude-code-sdk: uv add claude-code-sdk")
        print("2. Configured your API credentials")
        return 1
    
    # Test 2: Memory bank building
    build_ok = await test_memory_bank_build()
    
    if build_ok:
        print("\n✅ All tests passed! The backend integration is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))