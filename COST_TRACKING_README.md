# Memory Bank Cost Tracking System

The Memory Bank Builder now includes comprehensive cost tracking functionality that calculates the actual cost of multi-agent builds based on token usage from Claude Code sessions.

## Overview

The cost tracking system provides:
- **Real-time cost calculation** during multi-agent builds
- **Historical cost analysis** from Claude Code session logs  
- **Cost estimation** for planning builds
- **Model comparison** for cost optimization
- **Detailed breakdowns** by phase and component

## Components

### 1. Cost Calculator (`memory_bank_core/utils/cost_calculator.py`)
Calculates API costs based on Claude model pricing with support for:
- All Claude models (3 Haiku, 3.5 Haiku, 3.5 Sonnet, 4 Sonnet, 4 Opus)
- Token usage tracking (input, output, cache tokens)
- Phase and component cost breakdowns
- Cost estimation and ranges

### 2. Session Parser (`memory_bank_core/utils/session_parser.py`) 
Parses Claude Code JSONL session files to extract:
- Token usage from `~/.claude/projects/`
- Session metadata and timing
- Multi-agent session detection
- Recent usage analysis

### 3. Multi-Agent Builder Integration
The `MultiAgentMemoryBankBuilder` now includes:
- Automatic cost tracking during builds
- Cost metadata in build results
- Progress updates with cost information

## Usage

### Enable Cost Tracking in Multi-Agent Builds

```python
from memory_bank_core.builders.multi_agent_builder import MultiAgentMemoryBankBuilder
from memory_bank_core.models.build_job import BuildConfig

# Initialize with cost tracking enabled (default)
builder = MultiAgentMemoryBankBuilder(
    root_path=Path("."),
    enable_cost_tracking=True  # This is the default
)

# Build configuration
config = BuildConfig(
    repo_path="path/to/repo",
    output_path="path/to/output"
)

# Run build - cost tracking happens automatically
result = await builder.build_memory_bank(config, progress_callback)

# Access cost data from results
if "cost_tracking" in result.metadata:
    cost_data = result.metadata["cost_tracking"]
    print(f"Total cost: ${cost_data['total_cost']:.4f}")
    print(f"Tokens used: {cost_data['total_tokens']:,}")
```

### Analyze Historical Costs

```bash
# Analyze all memory bank sessions for this project
python analyze_memory_bank_costs.py

# Analyze specific session by ID
python analyze_memory_bank_costs.py --session abc12345
```

### Cost Estimation and Planning

```python
from memory_bank_core.utils.cost_calculator import CostCalculator, ClaudeModel

# Initialize calculator
calculator = CostCalculator(ClaudeModel.CLAUDE_4_SONNET)

# Estimate cost for a project
estimate = calculator.estimate_cost(
    num_components=15,
    avg_turns_architecture=200,
    avg_turns_per_component=100,
    avg_turns_per_validation=50
)

print(f"Estimated cost: ${estimate['total_estimated_cost']:.2f}")
print(f"Cost range: ${estimate['cost_range']['low']:.2f} - ${estimate['cost_range']['high']:.2f}")
```

### Run Cost Demonstrations

```bash
# See detailed cost examples and comparisons
python cost_demo.py

# Verify cost integration is working
python verify_cost_integration.py
```

## Cost Data Structure

Build results include cost tracking data in this format:

```json
{
  "cost_tracking": {
    "enabled": true,
    "total_cost": 12.5678,
    "input_tokens": 45000,
    "output_tokens": 15000,
    "total_tokens": 60000,
    "model_used": "claude-4-sonnet",
    "phase_costs": {
      "Phase 1: Architecture": 2.34,
      "Phase 2: Components": 7.89,
      "Phase 3: Validation": 2.34
    },
    "component_costs": {
      "user_service": 1.23,
      "payment_service": 2.45,
      "auth_service": 0.98
    }
  }
}
```

## Model Pricing (as of 2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3 Haiku | $0.25 | $1.25 |
| Claude 3.5 Haiku | $1.00 | $5.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 4 Sonnet | $3.00 | $15.00 |
| Claude 4 Opus | $15.00 | $75.00 |

## Cost Optimization Tips

1. **Model Selection**: Use Claude 3.5 Haiku for simple components (4x cheaper)
2. **Component Breakdown**: Avoid over-segmentation to reduce overhead
3. **Batch Processing**: Consider grouping smaller builds together
4. **Turn Limits**: Set appropriate max_turns to prevent runaway costs
5. **Cache Usage**: The system tracks cache tokens for accurate pricing

## Files and Scripts

- `analyze_memory_bank_costs.py` - Historical cost analysis
- `cost_demo.py` - Interactive cost demonstration
- `verify_cost_integration.py` - Verify system is working
- `memory_bank_core/utils/cost_calculator.py` - Core cost calculation
- `memory_bank_core/utils/session_parser.py` - Session log parsing
- `memory_bank_core/builders/multi_agent_builder.py` - Integrated builder

## Session Log Location

Claude Code stores session logs in:
```
~/.claude/projects/[project-hash]/[session-id].jsonl
```

The session parser automatically discovers and analyzes these files to calculate actual costs based on token usage.