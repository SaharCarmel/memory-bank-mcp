"""
Cost Calculator for Multi-Agent Memory Bank Builder

Calculates API costs based on token usage and Claude model pricing.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ClaudeModel(str, Enum):
    """Claude model options with pricing"""
    CLAUDE_4_OPUS = "claude-4-opus"
    CLAUDE_4_SONNET = "claude-4-sonnet" 
    CLAUDE_35_SONNET = "claude-3.5-sonnet"
    CLAUDE_35_HAIKU = "claude-3.5-haiku"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"


@dataclass
class ModelPricing:
    """Pricing information for a Claude model"""
    input_cost_per_million: float  # Cost per million input tokens
    output_cost_per_million: float  # Cost per million output tokens
    model_name: str


# Current Claude pricing as of 2025 (per million tokens)
CLAUDE_PRICING = {
    ClaudeModel.CLAUDE_4_OPUS: ModelPricing(15.00, 75.00, "Claude 4 Opus"),
    ClaudeModel.CLAUDE_4_SONNET: ModelPricing(3.00, 15.00, "Claude 4 Sonnet"),
    ClaudeModel.CLAUDE_35_SONNET: ModelPricing(3.00, 15.00, "Claude 3.5 Sonnet"),
    ClaudeModel.CLAUDE_35_HAIKU: ModelPricing(0.80, 4.00, "Claude 3.5 Haiku"),
    ClaudeModel.CLAUDE_3_OPUS: ModelPricing(15.00, 75.00, "Claude 3 Opus"),
    ClaudeModel.CLAUDE_3_SONNET: ModelPricing(3.00, 15.00, "Claude 3 Sonnet"),
    ClaudeModel.CLAUDE_3_HAIKU: ModelPricing(0.25, 1.25, "Claude 3 Haiku"),
}


@dataclass
class TokenUsage:
    """Token usage for a specific operation"""
    input_tokens: int
    output_tokens: int
    operation_name: str
    component_name: Optional[str] = None


@dataclass
class CostBreakdown:
    """Detailed cost breakdown"""
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    model_used: str
    phase_costs: Dict[str, float]
    component_costs: Dict[str, float]
    operation_costs: List[Dict[str, Any]]


class CostCalculator:
    """Calculates costs for multi-agent memory bank building operations"""
    
    def __init__(self, model: ClaudeModel = ClaudeModel.CLAUDE_4_SONNET):
        """
        Initialize cost calculator
        
        Args:
            model: Claude model being used (defaults to Claude 4 Sonnet)
        """
        self.model = model
        self.pricing = CLAUDE_PRICING[model]
        self.token_usages: List[TokenUsage] = []
        
    def add_token_usage(
        self, 
        input_tokens: int, 
        output_tokens: int, 
        operation_name: str, 
        component_name: Optional[str] = None
    ):
        """
        Add token usage for an operation
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            operation_name: Name of the operation (e.g., "architecture_analysis", "component_analysis", "validation")
            component_name: Name of the component (for component-specific operations)
        """
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            operation_name=operation_name,
            component_name=component_name
        )
        self.token_usages.append(usage)
        
        logger.debug(f"Added token usage: {operation_name} ({component_name or 'global'}) - "
                    f"Input: {input_tokens}, Output: {output_tokens}")
    
    def calculate_cost(self) -> CostBreakdown:
        """
        Calculate total cost based on accumulated token usage
        
        Returns:
            CostBreakdown with detailed cost information
        """
        if not self.token_usages:
            return CostBreakdown(
                total_input_tokens=0,
                total_output_tokens=0,
                total_tokens=0,
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
                model_used=self.pricing.model_name,
                phase_costs={},
                component_costs={},
                operation_costs=[]
            )
        
        total_input_tokens = sum(usage.input_tokens for usage in self.token_usages)
        total_output_tokens = sum(usage.output_tokens for usage in self.token_usages)
        total_tokens = total_input_tokens + total_output_tokens
        
        # Calculate costs
        input_cost = (total_input_tokens / 1_000_000) * self.pricing.input_cost_per_million
        output_cost = (total_output_tokens / 1_000_000) * self.pricing.output_cost_per_million
        total_cost = input_cost + output_cost
        
        # Calculate phase costs
        phase_costs = {}
        phase_mapping = {
            "architecture_analysis": "Phase 1: Architecture",
            "component_analysis": "Phase 2: Components", 
            "validation": "Phase 3: Validation"
        }
        
        for phase_key, phase_name in phase_mapping.items():
            phase_usages = [u for u in self.token_usages if phase_key in u.operation_name.lower()]
            if phase_usages:
                phase_input = sum(u.input_tokens for u in phase_usages)
                phase_output = sum(u.output_tokens for u in phase_usages)
                phase_input_cost = (phase_input / 1_000_000) * self.pricing.input_cost_per_million
                phase_output_cost = (phase_output / 1_000_000) * self.pricing.output_cost_per_million
                phase_costs[phase_name] = phase_input_cost + phase_output_cost
        
        # Calculate component costs
        component_costs = {}
        for usage in self.token_usages:
            if usage.component_name:
                if usage.component_name not in component_costs:
                    component_costs[usage.component_name] = 0.0
                
                comp_input_cost = (usage.input_tokens / 1_000_000) * self.pricing.input_cost_per_million
                comp_output_cost = (usage.output_tokens / 1_000_000) * self.pricing.output_cost_per_million
                component_costs[usage.component_name] += comp_input_cost + comp_output_cost
        
        # Create operation cost details
        operation_costs = []
        for usage in self.token_usages:
            op_input_cost = (usage.input_tokens / 1_000_000) * self.pricing.input_cost_per_million
            op_output_cost = (usage.output_tokens / 1_000_000) * self.pricing.output_cost_per_million
            op_total_cost = op_input_cost + op_output_cost
            
            operation_costs.append({
                "operation": usage.operation_name,
                "component": usage.component_name,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cost": op_total_cost
            })
        
        return CostBreakdown(
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model_used=self.pricing.model_name,
            phase_costs=phase_costs,
            component_costs=component_costs,
            operation_costs=operation_costs
        )
    
    def estimate_cost(
        self, 
        num_components: int = 10,
        avg_turns_architecture: int = 150,
        avg_turns_per_component: int = 75,
        avg_turns_per_validation: int = 50,
        avg_tokens_per_turn: int = 2000  # Conservative estimate
    ) -> Dict[str, Any]:
        """
        Estimate cost for a multi-agent build before running
        
        Args:
            num_components: Estimated number of components
            avg_turns_architecture: Average turns for architecture analysis
            avg_turns_per_component: Average turns per component
            avg_turns_per_validation: Average turns per validation
            avg_tokens_per_turn: Average tokens (input+output) per turn
            
        Returns:
            Dictionary with cost estimates
        """
        # Estimate token distribution (roughly 60% input, 40% output)
        input_ratio = 0.6
        output_ratio = 0.4
        
        # Phase 1: Architecture
        arch_total_tokens = avg_turns_architecture * avg_tokens_per_turn
        arch_input_tokens = int(arch_total_tokens * input_ratio)
        arch_output_tokens = int(arch_total_tokens * output_ratio)
        arch_cost = ((arch_input_tokens / 1_000_000) * self.pricing.input_cost_per_million + 
                    (arch_output_tokens / 1_000_000) * self.pricing.output_cost_per_million)
        
        # Phase 2: Components
        comp_total_tokens_per_comp = avg_turns_per_component * avg_tokens_per_turn
        comp_input_tokens_per_comp = int(comp_total_tokens_per_comp * input_ratio)
        comp_output_tokens_per_comp = int(comp_total_tokens_per_comp * output_ratio)
        comp_cost_per_comp = ((comp_input_tokens_per_comp / 1_000_000) * self.pricing.input_cost_per_million + 
                             (comp_output_tokens_per_comp / 1_000_000) * self.pricing.output_cost_per_million)
        comp_total_cost = comp_cost_per_comp * num_components
        
        # Phase 3: Validation
        val_total_tokens_per_comp = avg_turns_per_validation * avg_tokens_per_turn
        val_input_tokens_per_comp = int(val_total_tokens_per_comp * input_ratio)
        val_output_tokens_per_comp = int(val_total_tokens_per_comp * output_ratio)
        val_cost_per_comp = ((val_input_tokens_per_comp / 1_000_000) * self.pricing.input_cost_per_million + 
                            (val_output_tokens_per_comp / 1_000_000) * self.pricing.output_cost_per_million)
        val_total_cost = val_cost_per_comp * num_components
        
        total_estimated_cost = arch_cost + comp_total_cost + val_total_cost
        
        return {
            "model": self.pricing.model_name,
            "estimated_components": num_components,
            "phase_estimates": {
                "architecture": {
                    "turns": avg_turns_architecture,
                    "tokens": arch_total_tokens,
                    "cost": arch_cost
                },
                "components": {
                    "turns_per_component": avg_turns_per_component,
                    "tokens_per_component": comp_total_tokens_per_comp,
                    "cost_per_component": comp_cost_per_comp,
                    "total_cost": comp_total_cost
                },
                "validation": {
                    "turns_per_component": avg_turns_per_validation,
                    "tokens_per_component": val_total_tokens_per_comp,
                    "cost_per_component": val_cost_per_comp,
                    "total_cost": val_total_cost
                }
            },
            "total_estimated_cost": total_estimated_cost,
            "cost_range": {
                "low": total_estimated_cost * 0.7,  # 30% less than estimate
                "high": total_estimated_cost * 1.5   # 50% more than estimate
            }
        }
    
    def save_cost_report(self, output_path: Path, build_metadata: Optional[Dict] = None):
        """
        Save detailed cost report to file
        
        Args:
            output_path: Path to save the cost report
            build_metadata: Optional metadata from the build process
        """
        cost_breakdown = self.calculate_cost()
        
        report_data = {
            "cost_analysis": {
                "model_used": cost_breakdown.model_used,
                "pricing_per_million_tokens": {
                    "input": self.pricing.input_cost_per_million,
                    "output": self.pricing.output_cost_per_million
                },
                "token_usage": {
                    "total_input_tokens": cost_breakdown.total_input_tokens,
                    "total_output_tokens": cost_breakdown.total_output_tokens,
                    "total_tokens": cost_breakdown.total_tokens
                },
                "costs": {
                    "input_cost": round(cost_breakdown.input_cost, 4),
                    "output_cost": round(cost_breakdown.output_cost, 4),
                    "total_cost": round(cost_breakdown.total_cost, 4)
                },
                "phase_breakdown": {
                    phase: round(cost, 4) for phase, cost in cost_breakdown.phase_costs.items()
                },
                "component_breakdown": {
                    comp: round(cost, 4) for comp, cost in cost_breakdown.component_costs.items()
                },
                "operation_details": cost_breakdown.operation_costs
            },
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "calculator_version": "1.0.0",
                "pricing_date": "2025-01-22"
            }
        }
        
        if build_metadata:
            report_data["build_metadata"] = build_metadata
        
        cost_report_path = output_path / "cost_analysis.json"
        with open(cost_report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Cost report saved to: {cost_report_path}")
        
        return cost_report_path
    
    def print_cost_summary(self):
        """Print a formatted cost summary to console"""
        cost_breakdown = self.calculate_cost()
        
        print("\n" + "=" * 60)
        print(f"💰 COST ANALYSIS - {cost_breakdown.model_used}")
        print("=" * 60)
        
        if cost_breakdown.total_cost == 0:
            print("No token usage recorded - no costs incurred.")
            return
        
        print(f"📊 Token Usage:")
        print(f"   • Input Tokens:  {cost_breakdown.total_input_tokens:,}")
        print(f"   • Output Tokens: {cost_breakdown.total_output_tokens:,}")
        print(f"   • Total Tokens:  {cost_breakdown.total_tokens:,}")
        
        print(f"\n💵 Cost Breakdown:")
        print(f"   • Input Cost:   ${cost_breakdown.input_cost:.4f}")
        print(f"   • Output Cost:  ${cost_breakdown.output_cost:.4f}")
        print(f"   • TOTAL COST:   ${cost_breakdown.total_cost:.4f}")
        
        if cost_breakdown.phase_costs:
            print(f"\n🔍 Phase Costs:")
            for phase, cost in cost_breakdown.phase_costs.items():
                print(f"   • {phase}: ${cost:.4f}")
        
        if cost_breakdown.component_costs:
            print(f"\n🧩 Top Component Costs:")
            sorted_comps = sorted(cost_breakdown.component_costs.items(), 
                                key=lambda x: x[1], reverse=True)
            for comp, cost in sorted_comps[:5]:  # Show top 5
                print(f"   • {comp}: ${cost:.4f}")
            if len(sorted_comps) > 5:
                print(f"   ... and {len(sorted_comps) - 5} more components")
        
        print("=" * 60)