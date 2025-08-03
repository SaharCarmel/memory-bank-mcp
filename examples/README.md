# Memory Bank Examples

This directory contains example projects and their generated memory banks to demonstrate MemBankBuilder's capabilities.

## Available Examples

### 1. [Simple Python Script](simple-python-script/)
**Type**: Basic Python application
**Complexity**: Beginner
**Features**:
- Single-file implementation
- Class-based design
- Unit testing with pytest
- Error handling patterns

**Generated Memory Bank Highlights**:
- Architecture pattern identification (Monolithic Script)
- Design pattern recognition (Facade, Strategy, Guard Clauses)  
- Test coverage analysis
- Development task extraction

### 2. [React Todo App](react-todo-app/)
**Type**: Modern React SPA
**Complexity**: Intermediate
**Features**:
- Component-based architecture
- React Hooks and Context API
- Local storage persistence
- Responsive design

**Generated Memory Bank Highlights**:
- Component relationship mapping
- State management pattern analysis
- React best practices identification
- Data flow documentation

## How to Use These Examples

### 1. Study the Examples
```bash
# Explore the source code
ls examples/simple-python-script/
cat examples/simple-python-script/calculator.py
```

### 2. Generate Memory Banks
```bash
# Generate memory bank for Python example
uv run python -m memory_bank_core build examples/simple-python-script --output-name python-example

# Generate memory bank for React example  
uv run python -m memory_bank_core build examples/react-todo-app --output-name react-example
```

### 3. Compare Results
```bash
# View generated memory banks
ls python-example_memory_bank/memory-bank/
ls react-example_memory_bank/memory-bank/

# Read the generated analysis
cat python-example_memory_bank/memory-bank/systemPatterns.md
cat react-example_memory_bank/memory-bank/systemPatterns.md
```

## What You'll Learn

### Architecture Pattern Recognition
- How MemBankBuilder identifies common patterns (MVC, Component-based, etc.)
- Pattern-specific insights and recommendations
- Architecture evolution suggestions

### Technology Context Analysis
- Framework and library identification
- Dependency analysis and version tracking
- Technology stack recommendations

### Development Process Insights
- Current development status assessment
- Active work identification
- Next steps and improvement suggestions

### Code Quality Assessment
- Test coverage analysis
- Code organization evaluation
- Best practices compliance checking

## Example Output Structure

Each generated memory bank contains:

```
example_memory_bank/
├── memory-bank/
│   ├── projectbrief.md      # 📋 Project overview and goals
│   ├── productContext.md    # 👥 User needs and use cases  
│   ├── systemPatterns.md    # 🏗️ Architecture and patterns
│   ├── techContext.md       # ⚙️ Technology stack details
│   ├── activeContext.md     # 🔄 Current development state
│   ├── progress.md          # ✅ Implementation status
│   └── tasks/               # 📝 Development tasks
├── logs/                    # 📊 Build logs and metadata
└── generation_summary.json  # 📈 Analysis summary
```

## Expected Analysis Quality

### Simple Projects (like Python script)
- **Focus**: Core functionality and patterns
- **Depth**: Thorough analysis despite simplicity
- **Insights**: Best practices and improvement suggestions
- **Time**: ~2-5 minutes to generate

### Complex Projects (like React app)
- **Focus**: Architecture and component relationships
- **Depth**: Multi-layered analysis (components, state, data flow)
- **Insights**: Framework-specific patterns and optimizations
- **Time**: ~5-15 minutes to generate

## Creating Your Own Examples

Want to add an example? Follow this structure:

```
examples/your-example/
├── README.md                # Example description and insights
├── [source-code-files]      # The actual project to analyze
└── sample-output/           # Optional: sample memory bank output
    └── memory-bank/
        ├── projectbrief.md
        ├── systemPatterns.md
        └── ...
```

### Example README Template

```markdown
# Your Example Name

Brief description of the project and what it demonstrates.

## Source Structure
[Directory tree]

## Key Features
- Feature 1
- Feature 2

## Generated Insights
- Insight 1
- Insight 2

## Command to Generate
```bash
uv run python -m memory_bank_core build examples/your-example --output-name your-analysis
```
```

## Best Practices for Examples

1. **Keep Examples Focused**: Each example should demonstrate specific patterns or technologies
2. **Include Documentation**: Well-documented code produces better memory banks
3. **Vary Complexity**: Range from simple to complex projects
4. **Real-World Relevance**: Use patterns and structures common in actual projects
5. **Clear Structure**: Organized code leads to clearer analysis

## Next Steps

After exploring examples:
1. Try generating memory banks for your own projects
2. Compare the analysis with your understanding
3. Use insights for documentation and onboarding
4. Share interesting results with the community

These examples show MemBankBuilder's ability to understand and document projects across different languages, frameworks, and complexity levels.