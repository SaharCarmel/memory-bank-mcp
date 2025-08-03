# Contributing to MemBankBuilder

Thank you for your interest in contributing to MemBankBuilder! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/memory-bank-builder.git
   cd memory-bank-builder
   ```
3. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+ 
- Node.js 18+
- UV (for Python dependency management)

### Backend Setup
```bash
cd backend
uv venv
uv sync
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Core Library Setup
```bash
cd core
uv sync
```

## 🧪 Testing

Run tests before submitting:

```bash
# Backend tests
cd backend && uv run pytest

# Frontend tests  
cd frontend && npm test

# Core library tests
cd core && uv run pytest
```

## 📝 Code Style

- **Python**: Follow PEP 8, use type hints
- **JavaScript/React**: Follow ESLint configuration
- **Commit messages**: Use conventional commits format

Example commit message:
```
feat(core): add support for custom agents

- Add agent interface for extensibility
- Update builder to support plugin system
- Add tests for new agent types
```

## 🎯 Types of Contributions

### 🐛 Bug Reports
Use the bug report template and include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details

### ✨ Feature Requests
Use the feature request template and include:
- Clear use case description
- Proposed solution
- Alternative solutions considered

### 🔧 Code Contributions
- Follow the development setup above
- Add tests for new functionality
- Update documentation as needed
- Ensure all checks pass

## 📋 Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Run the full test suite**
4. **Update CHANGELOG.md** if applicable
5. **Submit pull request** with clear description

### PR Requirements
- [ ] Tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Code follows project style
- [ ] PR description explains changes

## 🏗️ Project Structure

```
memory-bank-builder/
├── backend/           # FastAPI server
├── frontend/          # React dashboard
├── core/              # Core Python library
├── action/            # GitHub Action
├── deployment/        # Deployment configs
├── docs/              # Documentation
├── examples/          # Usage examples
└── tests/             # Integration tests
```

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and experiences
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)

## 📚 Resources

- [Documentation](docs/)
- [API Reference](docs/api.md)
- [Examples](examples/)
- [Discord Community](https://discord.gg/membank-builder)

## ❓ Questions?

- Check existing [issues](https://github.com/membank-builder/memory-bank-builder/issues)
- Join our [Discord](https://discord.gg/membank-builder)
- Email: contributors@membank-builder.org

## 🙏 Recognition

Contributors are recognized in:
- README.md contributors section
- Annual contributor spotlight
- Project releases

Thank you for helping make MemBankBuilder better! 🎉