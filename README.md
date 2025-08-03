# MemBankBuilder 🧠

**Transform any codebase into a comprehensive memory bank using AI-powered analysis**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=github-actions)](https://github.com/marketplace/actions/memory-bank-builder)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue?logo=docker)](https://hub.docker.com/r/membank/builder)

MemBankBuilder analyzes your codebase and generates detailed documentation including project context, architecture patterns, technical decisions, and development progress. Perfect for onboarding, knowledge transfer, and maintaining project understanding.

## ✨ Features

- **🔍 Deep Code Analysis** - AI-powered repository analysis using Claude
- **📚 Structured Documentation** - Generates comprehensive memory banks with consistent structure
- **🌐 Web Dashboard** - Interactive UI for managing and viewing memory banks
- **⚡ Real-time Updates** - Live build progress and streaming logs
- **🐳 Self-Hosted** - Deploy on your infrastructure with Docker
- **🔄 GitHub Action** - Automate memory bank generation in CI/CD
- **🎯 Multi-Agent System** - Advanced analysis with specialized AI agents

## 🚀 Quick Start

### GitHub Action (Recommended)

Add to your `.github/workflows/memory-bank.yml`:

```yaml
name: Build Memory Bank
on: [push, pull_request]

jobs:
  memory-bank:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: membank-builder/memory-bank-action@v1
        with:
          claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
          output-path: ./docs/memory-bank
```

### Docker (Self-Hosted)

```bash
# Clone the repository
git clone https://github.com/membank-builder/memory-bank-builder.git
cd memory-bank-builder

# Start with Docker Compose
docker-compose up -d

# Access the dashboard
open http://localhost:3000
```

### CLI Installation

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
├── backend/             # FastAPI server
├── frontend/            # React dashboard
├── core/                # Core Python library
├── action/              # GitHub Action
├── deployment/          # Docker & K8s configs
├── docs/                # Documentation
└── examples/            # Usage examples
```

## 🌐 Deployment Options

### 1. Docker Compose (Simple)
Perfect for small teams and personal use:

```bash
docker-compose up -d
```

### 2. Kubernetes (Enterprise)
Scalable deployment with Helm:

```bash
helm install membank-builder ./deployment/kubernetes/chart
```

### 3. Cloud Providers
- [AWS ECS Guide](docs/deployment/aws.md)
- [Google Cloud Run Guide](docs/deployment/gcp.md)
- [Azure Container Instances Guide](docs/deployment/azure.md)

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
from core import CoreMemoryBankBuilder, BuildConfig, BuildMode

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

## 🤖 GitHub Action Advanced Usage

```yaml
- uses: membank-builder/memory-bank-action@v1
  with:
    claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
    output-path: ./docs/memory-bank
    mode: 'incremental'  # or 'full'
    max-turns: 5000
    custom-prompt: './custom-prompt.md'
    include-patterns: '**/*.py,**/*.js,**/*.md'
    exclude-patterns: '**/node_modules/**,**/.git/**'
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
cd core && uv sync
```

### Running Locally

```bash
# Start backend
cd backend && uv run python main.py

# Start frontend (new terminal)
cd frontend && npm run dev

# Test CLI
cd core && uv run python -m core build /path/to/test/repo
```

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Self-Hosted Deployment](docs/deployment.md)
- [Custom Agent Development](docs/agents.md)
- [Configuration Reference](docs/configuration.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

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