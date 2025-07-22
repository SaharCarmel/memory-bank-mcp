"""
Simple Cost Calculation Demo for Memory Bank Building
"""

from memory_bank_core.utils.cost_calculator import CostCalculator, ClaudeModel


def demo_cost_calculations():
    """Demonstrate cost calculations for multi-agent memory bank building"""
    
    print("💰 Memory Bank Building Cost Calculator")
    print("=" * 60)
    
    # Initialize calculator with Claude 4 Sonnet (current default)
    calculator = CostCalculator(ClaudeModel.CLAUDE_4_SONNET)
    
    print("📊 Cost Estimates for Multi-Agent Memory Bank Building")
    print("-" * 60)
    
    # Small project estimate
    small_project = calculator.estimate_cost(
        num_components=5,
        avg_turns_architecture=150,
        avg_turns_per_component=75, 
        avg_turns_per_validation=50,
        avg_tokens_per_turn=2000
    )
    
    # Medium project estimate
    medium_project = calculator.estimate_cost(
        num_components=15,
        avg_turns_architecture=200,
        avg_turns_per_component=100,
        avg_turns_per_validation=50,
        avg_tokens_per_turn=2000
    )
    
    # Large project estimate
    large_project = calculator.estimate_cost(
        num_components=30,
        avg_turns_architecture=200,
        avg_turns_per_component=100,
        avg_turns_per_validation=75,
        avg_tokens_per_turn=2500
    )
    
    projects = [
        ("Small Project (5 components)", small_project),
        ("Medium Project (15 components)", medium_project),
        ("Large Project (30 components)", large_project)
    ]
    
    for project_name, estimate in projects:
        print(f"\n🏗️  {project_name}")
        print(f"    Architecture Phase: ${estimate['phase_estimates']['architecture']['cost']:.2f}")
        print(f"    Components Phase:   ${estimate['phase_estimates']['components']['total_cost']:.2f}")
        print(f"    Validation Phase:   ${estimate['phase_estimates']['validation']['total_cost']:.2f}")
        print(f"    TOTAL COST:         ${estimate['total_estimated_cost']:.2f}")
        print(f"    Cost Range:         ${estimate['cost_range']['low']:.2f} - ${estimate['cost_range']['high']:.2f}")
    
    # Model comparison
    print("\n🏷️  Cost Comparison by Claude Model (Medium Project)")
    print("-" * 60)
    
    models = [
        (ClaudeModel.CLAUDE_3_HAIKU, "Claude 3 Haiku (Cheapest)"),
        (ClaudeModel.CLAUDE_35_HAIKU, "Claude 3.5 Haiku (Fast)"),
        (ClaudeModel.CLAUDE_35_SONNET, "Claude 3.5 Sonnet (Balanced)"),
        (ClaudeModel.CLAUDE_4_SONNET, "Claude 4 Sonnet (Current)"),
        (ClaudeModel.CLAUDE_4_OPUS, "Claude 4 Opus (Most Advanced)")
    ]
    
    for model, description in models:
        calc = CostCalculator(model)
        estimate = calc.estimate_cost(num_components=15)
        savings = ((medium_project['total_estimated_cost'] - estimate['total_estimated_cost']) / 
                  medium_project['total_estimated_cost'] * 100)
        
        print(f"{description:30}: ${estimate['total_estimated_cost']:7.2f} ", end="")
        if savings > 0:
            print(f"({savings:+.0f}% vs Sonnet 4)")
        elif savings < 0:
            print(f"({savings:+.0f}% vs Sonnet 4)")
        else:
            print("(baseline)")
    
    # Cost per component breakdown
    print(f"\n📊 Per-Component Cost Breakdown (Claude 4 Sonnet)")
    print("-" * 60)
    
    calc = CostCalculator(ClaudeModel.CLAUDE_4_SONNET)
    single_comp = calc.estimate_cost(num_components=1)
    
    print(f"Architecture Analysis (one-time): ${single_comp['phase_estimates']['architecture']['cost']:.2f}")
    print(f"Per Component Analysis:           ${single_comp['phase_estimates']['components']['cost_per_component']:.2f}")
    print(f"Per Component Validation:         ${single_comp['phase_estimates']['validation']['cost_per_component']:.2f}")
    print(f"Total per Additional Component:   ${single_comp['phase_estimates']['components']['cost_per_component'] + single_comp['phase_estimates']['validation']['cost_per_component']:.2f}")
    
    # Real token usage simulation
    print(f"\n🧪 Simulated Real Usage Example")
    print("-" * 60)
    
    # Simulate a realistic multi-agent build
    sim_calculator = CostCalculator(ClaudeModel.CLAUDE_4_SONNET)
    
    # Phase 1: Architecture (actual usage pattern)
    sim_calculator.add_token_usage(25000, 8000, "architecture_analysis")
    
    # Phase 2: Components (5 components with varying complexity)  
    component_usages = [
        (15000, 5000, "user_service"),
        (18000, 6000, "payment_service"), 
        (12000, 4000, "auth_service"),
        (20000, 7000, "product_service"),
        (14000, 4500, "notification_service")
    ]
    
    for input_tokens, output_tokens, component in component_usages:
        sim_calculator.add_token_usage(input_tokens, output_tokens, "component_analysis", component)
    
    # Phase 3: Validation (5 components)
    for _, _, component in component_usages:
        sim_calculator.add_token_usage(8000, 3000, "validation", component)
    
    sim_breakdown = sim_calculator.calculate_cost()
    
    print(f"Simulated Build Results:")
    print(f"  Total Input Tokens:  {sim_breakdown.total_input_tokens:,}")
    print(f"  Total Output Tokens: {sim_breakdown.total_output_tokens:,}")
    print(f"  Total Tokens:        {sim_breakdown.total_tokens:,}")
    print(f"  Total Cost:          ${sim_breakdown.total_cost:.4f}")
    
    if sim_breakdown.phase_costs:
        print(f"\n  Phase Breakdown:")
        for phase, cost in sim_breakdown.phase_costs.items():
            print(f"    {phase}: ${cost:.4f}")
    
    if sim_breakdown.component_costs:
        print(f"\n  Component Breakdown:")
        sorted_components = sorted(sim_breakdown.component_costs.items(), 
                                 key=lambda x: x[1], reverse=True)
        for component, cost in sorted_components:
            print(f"    {component}: ${cost:.4f}")
    
    # Monthly budget estimates
    print(f"\n📅 Monthly Budget Estimates")
    print("-" * 60)
    
    monthly_scenarios = [
        ("Light usage (2 builds/month)", 2, medium_project['total_estimated_cost']),
        ("Regular usage (5 builds/month)", 5, medium_project['total_estimated_cost']),  
        ("Heavy usage (10 builds/month)", 10, medium_project['total_estimated_cost']),
        ("Enterprise usage (20 builds/month)", 20, medium_project['total_estimated_cost'])
    ]
    
    for scenario, builds, cost_per_build in monthly_scenarios:
        monthly_cost = builds * cost_per_build
        print(f"{scenario:30}: ${monthly_cost:7.2f}/month")
    
    print("\n" + "=" * 60)
    print("💡 Cost Optimization Tips:")
    print("   • Use Claude 3.5 Haiku for simple components (4x cheaper)")
    print("   • Cache system prompts to reduce input token costs")
    print("   • Optimize component breakdown to avoid over-segmentation")
    print("   • Use batch processing for non-urgent builds (50% discount)")
    print("   • Consider Claude Pro subscription for heavy usage")
    print("=" * 60)


if __name__ == "__main__":
    demo_cost_calculations()