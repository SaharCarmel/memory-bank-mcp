# Troubleshooting Guide

Common issues and solutions when using MemBankBuilder CLI.

## Installation Issues

### UV Installation Problems

**Problem**: `uv: command not found`
```bash
# Solution: Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

**Problem**: UV installed but not in PATH
```bash
# Solution: Add UV to PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Python Version Issues

**Problem**: `Python 3.11+ required`
```bash
# Check Python version
python3 --version

# Install Python 3.11+ via UV
uv python install 3.11
uv python use 3.11
```

## Runtime Issues

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'memory_bank_core'`
```bash
# Solution: Ensure proper installation
cd memory_bank_core
uv sync

# Verify installation
uv run python -c "import memory_bank_core; print('✅ Import successful')"
```

**Problem**: `ModuleNotFoundError: No module named 'pydantic'`
```bash
# Solution: Reinstall dependencies
cd memory_bank_core
uv sync --force
```

### API Key Issues

**Problem**: `Missing Claude API key`
```bash
# Solution: Set environment variable
export CLAUDE_API_KEY=your-api-key-here

# Verify it's set
echo $CLAUDE_API_KEY

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export CLAUDE_API_KEY=your-api-key-here' >> ~/.bashrc
```

**Problem**: `Invalid API key format`
```bash
# Verify API key format (should start with 'sk-ant-')
echo $CLAUDE_API_KEY | head -c 10

# Get new API key from: https://console.anthropic.com/
```

### Build Failures

**Problem**: `Build failed: Repository path does not exist`
```bash
# Solution: Check path exists and is accessible
ls -la /path/to/your/repo
cd /path/to/your/repo && pwd  # Verify absolute path
```

**Problem**: `Build failed: Permission denied`
```bash
# Solution: Check repository permissions
chmod -R 755 /path/to/your/repo

# Or run with sudo if needed (not recommended)
sudo uv run python -m memory_bank_core build /path/to/repo
```

**Problem**: `Build timeout or hangs`
```bash
# Solution 1: Enable verbose logging
uv run python -m memory_bank_core --verbose build /path/to/repo

# Solution 2: Try legacy mode
uv run python -m memory_bank_core build /path/to/repo --legacy

# Solution 3: Check for large files
find /path/to/repo -size +100M -type f
```

## Performance Issues

### Slow Build Times

**Problem**: Build takes very long (>30 minutes)
```bash
# Solution 1: Check repository size
du -sh /path/to/repo

# Solution 2: Exclude large directories
# Create .gitignore or exclude patterns in your repo

# Solution 3: Use incremental updates
uv run python -m memory_bank_core update /path/to/repo existing-memory-bank
```

**Problem**: High memory usage
```bash
# Solution 1: Monitor memory usage
htop  # or Activity Monitor on Mac

# Solution 2: Process smaller repositories
# Split large monorepos into smaller components

# Solution 3: Reduce concurrent jobs
uv run python -m memory_bank_core worker --max-jobs 1
```

### Disk Space Issues

**Problem**: `No space left on device`
```bash
# Solution 1: Check disk space
df -h

# Solution 2: Clean up old memory banks
rm -rf old_memory_bank_directories/

# Solution 3: Use custom output directory on larger disk
uv run python -m memory_bank_core --root-path /path/to/larger/disk build /repo
```

## Output Issues

### Empty or Incomplete Memory Banks

**Problem**: Memory bank created but files are empty
```bash
# Solution 1: Check build logs
ls -la your-repo_memory_bank/logs/
cat your-repo_memory_bank/logs/latest.log

# Solution 2: Verify API key has credits
# Check your Anthropic console

# Solution 3: Try with verbose logging
uv run python -m memory_bank_core --verbose build /path/to/repo
```

**Problem**: Missing files in memory bank
```bash
# Expected structure:
ls your-repo_memory_bank/memory-bank/
# Should show: projectbrief.md, productContext.md, etc.

# Solution: Check if build completed successfully
cat your-repo_memory_bank/generation_summary.json
```

### Encoding Issues

**Problem**: `UnicodeDecodeError` during build
```bash
# Solution 1: Check for binary files in repo
file /path/to/repo/* | grep -v text

# Solution 2: Set proper locale
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# Solution 3: Use legacy mode
uv run python -m memory_bank_core build /path/to/repo --legacy
```

## System-Specific Issues

### macOS Issues

**Problem**: `Operation not permitted` errors
```bash
# Solution: Grant Full Disk Access to Terminal
# System Preferences > Security & Privacy > Privacy > Full Disk Access
# Add Terminal.app or iTerm.app
```

**Problem**: `quarantine` warnings for downloaded files
```bash
# Solution: Remove quarantine attribute
xattr -r -d com.apple.quarantine memory-bank-builder/
```

### Windows Issues

**Problem**: Path length limitations
```bash
# Solution: Use shorter paths or enable long path support
# Run as Administrator:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

**Problem**: PowerShell execution policy
```bash
# Solution: Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux Issues

**Problem**: Missing system dependencies
```bash
# Solution: Install required packages (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv build-essential

# For other distributions, adjust package manager and names
```

## Advanced Debugging

### Enable Debug Logging

```bash
# Maximum verbosity
export PYTHONPATH=/path/to/memory-bank-builder
uv run python -m memory_bank_core --verbose build /repo 2>&1 | tee debug.log
```

### Check Process Status

```bash
# Monitor running processes
ps aux | grep memory_bank_core

# Check memory usage
top -p $(pgrep -f memory_bank_core)
```

### Network Issues

```bash
# Test Claude API connectivity
curl -H "Authorization: Bearer $CLAUDE_API_KEY" https://api.anthropic.com/v1/messages

# Check DNS resolution
nslookup api.anthropic.com
```

## Getting Help

### Log Analysis

When reporting issues, include:

```bash
# System information
uv --version
python3 --version
uname -a  # Linux/Mac
systeminfo  # Windows

# Memory bank build logs
cat your-repo_memory_bank/logs/latest.log

# Error messages with full traceback
uv run python -m memory_bank_core --verbose build /repo 2>&1
```

### Common Log Patterns

**Look for these patterns in logs:**

- `✅ Success patterns`: "Build completed successfully", "Memory bank generated"
- `⚠️ Warning patterns`: "Timeout", "Rate limited", "Large file skipped" 
- `❌ Error patterns`: "Failed to", "Error:", "Exception:", "Traceback"

### Reporting Bugs

Include this information when reporting issues:

1. **Command used**: Exact command that failed
2. **Error message**: Full error output with traceback
3. **System info**: OS, Python version, UV version
4. **Repository info**: Size, type, any unusual characteristics
5. **Logs**: Relevant log excerpts

### Community Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/membank-builder/memory-bank-builder/issues)
- **Discussions**: [Ask questions and share tips](https://github.com/membank-builder/memory-bank-builder/discussions)

## Quick Fixes Checklist

Before deep debugging, try these quick fixes:

- [ ] Restart terminal/command prompt
- [ ] Verify `CLAUDE_API_KEY` is set correctly
- [ ] Check internet connectivity
- [ ] Ensure repository path is accessible
- [ ] Try with `--verbose` flag
- [ ] Test with a small, simple repository
- [ ] Check available disk space
- [ ] Update to latest version: `git pull && cd memory_bank_core && uv sync`

Most issues are resolved by checking API key configuration and ensuring proper repository access permissions.