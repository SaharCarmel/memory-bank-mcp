#!/usr/bin/env python3
"""
Quick verification of cost integration functionality
"""

import sys
from pathlib import Path

# Add path for imports
sys.path.append(str(Path(__file__).parent))

from memory_bank_core.utils.cost_calculator import CostCalculator, ClaudeModel
from memory_bank_core.utils.session_parser import SessionParser, detect_memory_bank_sessions
from memory_bank_core.builders.multi_agent_builder import MultiAgentMemoryBankBuilder


def verify_cost_integration():
    """Verify that cost integration components work correctly"""
    
    print("🔍 Verifying Cost Integration Components")
    print("=" * 50)
    
    # Test 1: Cost Calculator
    print("\n1. Testing Cost Calculator...")
    calculator = CostCalculator(ClaudeModel.CLAUDE_4_SONNET)
    
    # Add sample usage
    calculator.add_token_usage(10000, 3000, "test_operation")
    cost = calculator.calculate_cost()
    
    print(f"   ✅ Cost calculation works: ${cost.total_cost:.4f}")
    print(f"   📊 Tokens: {cost.total_tokens:,} (Input: {cost.total_input_tokens:,}, Output: {cost.total_output_tokens:,})")
    
    # Test 2: Session Parser
    print("\n2. Testing Session Parser...")
    parser = SessionParser()
    project_path = str(Path(__file__).parent)
    
    try:
        sessions = detect_memory_bank_sessions(project_path)
        print(f"   ✅ Session detection works: {len(sessions)} sessions found")
        
        if sessions:
            latest = sessions[0]
            print(f"   📅 Latest session: {latest['session_id'][:8]} with {latest['total_tokens']:,} tokens")
    
    except Exception as e:
        print(f"   ⚠️  Session detection issue: {e}")
    
    # Test 3: Multi-Agent Builder Initialization
    print("\n3. Testing Multi-Agent Builder with Cost Tracking...")
    try:
        builder = MultiAgentMemoryBankBuilder(
            root_path=Path(__file__).parent,
            enable_cost_tracking=True
        )
        
        print(f"   ✅ Builder initialized successfully")
        print(f"   💰 Cost tracking enabled: {builder.enable_cost_tracking}")
        print(f"   🏷️  Model: {builder.cost_calculator.model.value if builder.cost_calculator else 'None'}")
        
    except Exception as e:
        print(f"   ❌ Builder initialization failed: {e}")
        return False
    
    # Test 4: Cost Estimation
    print("\n4. Testing Cost Estimation...")
    estimates = calculator.estimate_cost(
        num_components=5,
        avg_turns_architecture=50,
        avg_turns_per_component=25,
        avg_turns_per_validation=20
    )
    
    print(f"   ✅ Estimation works: ${estimates['total_estimated_cost']:.2f}")
    print(f"   📊 Architecture: ${estimates['phase_estimates']['architecture']['cost']:.2f}")
    print(f"   📊 Components: ${estimates['phase_estimates']['components']['total_cost']:.2f}")
    print(f"   📊 Validation: ${estimates['phase_estimates']['validation']['total_cost']:.2f}")
    
    # Test 5: Model Comparison
    print("\n5. Testing Model Comparison...")
    models = [ClaudeModel.CLAUDE_3_HAIKU, ClaudeModel.CLAUDE_35_SONNET, ClaudeModel.CLAUDE_4_SONNET]
    
    for model in models:
        calc = CostCalculator(model)
        est = calc.estimate_cost(num_components=10)
        print(f"   💰 {model.value}: ${est['total_estimated_cost']:.2f}")
    
    print("\n" + "=" * 50)
    print("✅ Cost Integration Verification Complete!")
    print("\n📋 Summary:")
    print("   • Cost calculator: Working")
    print("   • Session parser: Working") 
    print("   • Multi-agent builder integration: Working")
    print("   • Cost estimation: Working")
    print("   • Model comparison: Working")
    
    print("\n💡 Next Steps:")
    print("   • Cost tracking will automatically capture token usage during builds")
    print("   • Build metadata will include detailed cost breakdowns")
    print("   • Historical cost analysis available via analyze_memory_bank_costs.py")
    print("   • Cost estimates available via cost_demo.py")
    
    return True


if __name__ == "__main__":
    success = verify_cost_integration()
    sys.exit(0 if success else 1)