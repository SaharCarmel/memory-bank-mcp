# Simple Python Script Example

This example shows what MemBankBuilder generates for a basic Python script project.

## Source Code Structure

```
simple-python-script/
├── calculator.py          # Main calculator implementation
├── requirements.txt       # Project dependencies  
├── README.md             # Project documentation
└── tests/
    └── test_calculator.py # Unit tests
```

## Generated Memory Bank

The CLI command:
```bash
uv run python -m memory_bank_core build simple-python-script --output-name calculator-analysis
```

Generates this memory bank structure:

```
calculator-analysis_memory_bank/
├── memory-bank/
│   ├── projectbrief.md      # Project overview
│   ├── productContext.md    # User needs analysis
│   ├── systemPatterns.md    # Architecture patterns
│   ├── techContext.md       # Technology details
│   ├── activeContext.md     # Current state
│   ├── progress.md          # Implementation status
│   └── tasks/               # Development tasks
│       ├── _index.md
│       └── test-coverage.md
└── logs/                    # Build metadata
```

## Sample Generated Content

### projectbrief.md
```markdown
# Simple Calculator Project

## Overview
A lightweight Python calculator implementation with basic arithmetic operations and comprehensive unit testing.

## Core Requirements
- Perform basic arithmetic operations (add, subtract, multiply, divide)
- Handle edge cases (division by zero, invalid inputs)
- Maintain high test coverage
- Simple, clean API design

## Success Criteria
- All arithmetic operations work correctly
- Comprehensive error handling
- 100% test coverage
- Clear documentation
```

### systemPatterns.md
```markdown
# System Architecture

## Pattern Classification
**Monolithic Script Pattern** - Single-file implementation with clear separation of concerns

## Component Structure
- `Calculator` class: Core arithmetic operations
- Input validation: Type checking and error handling
- Test suite: Comprehensive unit test coverage

## Design Patterns Used
- **Facade Pattern**: Simple interface hiding complexity
- **Strategy Pattern**: Different operation methods
- **Guard Clauses**: Early returns for validation

## Dependencies
- Pure Python implementation (no external dependencies)
- pytest for testing framework
```

This example demonstrates how MemBankBuilder analyzes even simple projects to extract:
- Project purpose and requirements
- Architecture patterns
- Technology choices
- Implementation status
- Development tasks