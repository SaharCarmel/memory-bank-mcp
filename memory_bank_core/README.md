# MemBankBuilder 🧠

**CLI tool to transform any codebase into a comprehensive memory bank using AI-powered analysis**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MemBankBuilder is a command-line tool that analyzes your codebase and generates detailed documentation including project context, architecture patterns, technical decisions, and development progress. Perfect for onboarding, knowledge transfer, and maintaining project understanding.

## ✨ Features

- **🔍 Deep Code Analysis** - AI-powered repository analysis using Claude
- **📚 Structured Documentation** - Generates comprehensive memory banks with consistent structure
- **🌐 Web Dashboard** - Optional interactive UI for managing and viewing memory banks
- **⚡ Real-time Updates** - Live build progress and detailed logging
- **🖥️ Self-Hosted** - Deploy on your infrastructure
- **⚙️ Automation-Ready** - Easy integration with CI/CD pipelines
- **🎯 Multi-Agent System** - Advanced analysis with specialized AI agents

## 🚀 Quick Start

### CLI Installation (Recommended)

```bash
# Install with UV (recommended)
uv add memory-bank-builder

# Or with pip
pip install memory-bank-builder

# Build a memory bank
memory-bank build /path/to/your/repo
```

## 📁 What Gets Generated

Each memory bank contains:

```
your-repo_memory_bank/
├── projectbrief.md      # Project overview and goals
├── productContext.md    # User needs and problems solved
├── systemPatterns.md    # Architecture and design patterns
├── techContext.md       # Technologies and setup
├── activeContext.md     # Current focus and recent changes
├── progress.md          # Implementation status
└── tasks/              # Task tracking and management
    ├── _index.md
    └── *.md
```

## 🏗️ Architecture

```
memory-bank-builder/
├── backend/             # FastAPI server (optional web interface)
├── frontend/            # React dashboard (optional web interface)
├── memory_bank_core/    # Core Python library
├── docs/                # Documentation
└── examples/            # Usage examples
```

## 🌐 Deployment Options

### 1. Local CLI (Recommended)
Perfect for individual use and development:

```bash
# Install and use directly
uv add memory-bank-builder
memory-bank build /path/to/your/repo
```

### 2. Web Interface (Optional)
For teams wanting a web dashboard:

```bash
# Start backend
cd backend && uv run python main.py

# Start frontend (separate terminal)
cd frontend && npm run dev
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CLAUDE_API_KEY` | Claude API key (required) | - |
| `PORT` | Server port | `8000` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |
| `MAX_CONCURRENT_JOBS` | Max parallel builds | `3` |
| `OUTPUT_PATH` | Memory bank output directory | `./memory-banks` |

### Custom Configuration

Create a `.env` file:

```bash
CLAUDE_API_KEY=your-api-key-here
PORT=8000
MAX_CONCURRENT_JOBS=5
OUTPUT_PATH=/data/memory-banks
```

## 📖 Usage Examples

### Basic Memory Bank Generation

```python
from memory_bank_core import CoreMemoryBankBuilder, BuildConfig, BuildMode

builder = CoreMemoryBankBuilder("/output/path") 
config = BuildConfig(
    repo_path="/path/to/repo",
    output_path="/output/memory-bank",
    mode=BuildMode.FULL
)

result = await builder.build_memory_bank(config)
```

### Web API

```bash
# Start a build job
curl -X POST http://localhost:8000/api/memory-banks/build \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo", "output_name": "my-project"}'

# Check build status
curl http://localhost:8000/api/jobs/{job_id}
```

### CLI Commands

```bash
# Build memory bank
memory-bank build /path/to/repo --output-name my-project

# Update existing memory bank
memory-bank update /path/to/repo my-project

# List all memory banks
memory-bank list

# Start background worker
memory-bank worker --max-jobs 5
```

## 🤖 Advanced CLI Usage

```bash
# Build with custom options
memory-bank build /path/to/repo \
  --output-name my-project \
  --mode incremental \
  --max-turns 5000 \
  --include-patterns '**/*.py,**/*.js,**/*.md' \
  --exclude-patterns '**/node_modules/**,**/.git/**'
```

## 🔍 Memory Bank Structure

### Core Files

- **`projectbrief.md`** - High-level project overview, goals, and requirements
- **`productContext.md`** - User problems, use cases, and business value
- **`systemPatterns.md`** - Architecture patterns, design decisions, and component relationships
- **`techContext.md`** - Technologies used, dependencies, and setup instructions
- **`activeContext.md`** - Current development focus and recent changes
- **`progress.md`** - Implementation status, completed features, and known issues

### Task System

The `tasks/` directory contains:
- Individual task files with status tracking
- Development roadmap and planning
- Bug reports and technical debt items
- Feature specifications and requirements

## 🧪 Examples

Explore our example memory banks:

- [React App Example](examples/react-app/) - Frontend application memory bank
- [Python API Example](examples/python-api/) - Backend service memory bank  
- [Node.js Service Example](examples/nodejs-service/) - Microservice memory bank

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- UV (Python dependency manager)

### Setup

```bash
# Backend
cd backend && uv sync

# Frontend  
cd frontend && npm install

# Core library
cd memory_bank_core && uv sync
```

### Running Locally

```bash
# Start backend
cd backend && uv run python main.py

# Start frontend (new terminal)
cd frontend && npm run dev

# Test CLI
cd memory_bank_core && uv run python -m memory_bank_core build /path/to/test/repo
```

## 🧪 Testing Your Setup

### Quick Smoke Test
```bash
# Test all components quickly
cd backend && uv run python -c "from app.services.memory_bank_builder import MemoryBankBuilder; print('✅ Backend OK')" && \
cd ../frontend && npm run build > /dev/null 2>&1 && echo "✅ Frontend OK" && \
cd ../memory_bank_core && uv run python -m memory_bank_core --help > /dev/null && echo "✅ CLI OK" && \
echo "🎉 All systems working!"
```

### Individual Component Tests

**Test CLI:**
```bash
cd memory_bank_core
uv run python -m memory_bank_core --help        # Show available commands
uv run python -m memory_bank_core list          # List existing memory banks
```

**Test Backend:**
```bash
cd backend
uv run python main.py &                         # Start server
curl http://localhost:8000/docs                 # Open API documentation
curl http://localhost:8000/api/memory-banks     # Test API endpoint
```

**Test Frontend:**
```bash
cd frontend
npm run build                                    # Test production build
npm run dev                                      # Start development server (localhost:5173)
```

**Test Full Integration (Optional Web Interface):**
```bash
# 1. Start backend: cd backend && uv run python main.py
# 2. Start frontend: cd frontend && npm run dev  
# 3. Open http://localhost:5173 in browser
# 4. Create a memory bank through the web interface
```

### Expected Results
- ✅ CLI shows help and commands
- ✅ Backend starts on port 8000 
- ✅ Frontend builds without errors
- ✅ API docs accessible at `/docs`
- ✅ Web dashboard loads at localhost:5173

## 📚 Documentation

### Getting Started
- [CLI Usage Guide](docs/cli-usage.md) - Complete CLI reference and examples
- [Troubleshooting Guide](docs/troubleshooting.md) - Common issues and solutions

### Examples & Integration
- [Example Projects](examples/) - Sample projects and generated memory banks
- [Integration Guide](docs/integrations.md) - CI/CD, Git hooks, and automation

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Commit: `git commit -m 'feat: add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📊 Roadmap

- [ ] **Multi-language Support** - Support for more programming languages
- [ ] **Custom Templates** - User-defined memory bank templates
- [ ] **Integration Ecosystem** - Notion, Confluence, GitBook integrations
- [ ] **Performance Optimization** - Faster analysis for large repositories
- [ ] **Collaborative Features** - Team memory bank sharing and collaboration
- [ ] **Docker Support** - Containerized deployment options
- [ ] **GitHub Actions** - Automated CI/CD integration

## ❓ Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/membank-builder/memory-bank-builder/issues)
- 💬 [Discussions](https://github.com/membank-builder/memory-bank-builder/discussions)
- 📧 Email: support@membank-builder.org

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Claude](https://claude.ai) for AI-powered code analysis
- Inspired by the need for better code documentation and knowledge transfer
- Thanks to all our [contributors](https://github.com/membank-builder/memory-bank-builder/graphs/contributors)

---

**⭐ Star this repo if you find it useful!**

Made with ❤️ by the MemBankBuilder team