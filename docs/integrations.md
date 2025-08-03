# Integration Guide

Learn how to integrate MemBankBuilder into your development workflow, CI/CD pipelines, and documentation systems.

## Git Hooks Integration

### Post-Commit Hook
Automatically update memory banks when code changes:

```bash
#!/bin/bash
# .git/hooks/post-commit

# Update memory bank after each commit
echo "Updating memory bank..."
uv run python -m memory_bank_core update . project-memory-bank --no-wait

# Optional: Commit the updated memory bank
if [ -d "project-memory-bank_memory_bank" ]; then
    git add project-memory-bank_memory_bank/
    git commit -m "docs: update memory bank [skip ci]"
fi
```

### Pre-Push Hook
Generate fresh analysis before pushing:

```bash
#!/bin/bash
# .git/hooks/pre-push

echo "Generating fresh memory bank analysis..."
uv run python -m memory_bank_core build . --output-name pre-push-analysis

echo "Memory bank generated at: pre-push-analysis_memory_bank/"
echo "Review the analysis before continuing with push."
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/memory-bank.yml`:

```yaml
name: Generate Memory Bank

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  memory-bank:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Install MemBankBuilder
      run: |
        git clone https://github.com/membank-builder/memory-bank-builder.git
        cd memory-bank-builder/memory_bank_core
        uv sync
    
    - name: Generate Memory Bank
      env:
        CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
      run: |
        cd memory-bank-builder/memory_bank_core
        uv run python -m memory_bank_core build ${{ github.workspace }} --output-name ci-analysis
    
    - name: Upload Memory Bank
      uses: actions/upload-artifact@v4
      with:
        name: memory-bank-analysis
        path: memory-bank-builder/memory_bank_core/ci-analysis_memory_bank/
    
    - name: Comment on PR (if PR)
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');
          const path = './memory-bank-builder/memory_bank_core/ci-analysis_memory_bank/memory-bank/projectbrief.md';
          if (fs.existsSync(path)) {
            const content = fs.readFileSync(path, 'utf8');
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🧠 Memory Bank Analysis\n\n### Project Brief\n\`\`\`markdown\n${content.substring(0, 1000)}...\n\`\`\`\n\n[Full analysis available in workflow artifacts]`
            });
          }
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - analyze

memory-bank-analysis:
  stage: analyze
  image: python:3.11
  before_script:
    - apt-get update && apt-get install -y curl
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.cargo/bin:$PATH"
    - git clone https://github.com/membank-builder/memory-bank-builder.git
    - cd memory-bank-builder/memory_bank_core && uv sync
  script:
    - cd memory-bank-builder/memory_bank_core
    - uv run python -m memory_bank_core build $CI_PROJECT_DIR --output-name gitlab-analysis
  artifacts:
    paths:
      - memory-bank-builder/memory_bank_core/gitlab-analysis_memory_bank/
    expire_in: 1 week
  only:
    - main
    - merge_requests
```

### Jenkins Pipeline

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    environment {
        CLAUDE_API_KEY = credentials('claude-api-key')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'curl -LsSf https://astral.sh/uv/install.sh | sh'
                sh 'git clone https://github.com/membank-builder/memory-bank-builder.git'
                sh 'cd memory-bank-builder/memory_bank_core && ~/.cargo/bin/uv sync'
            }
        }
        
        stage('Generate Memory Bank') {
            steps {
                sh '''
                    cd memory-bank-builder/memory_bank_core
                    ~/.cargo/bin/uv run python -m memory_bank_core build ${WORKSPACE} --output-name jenkins-analysis
                '''
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'memory-bank-builder/memory_bank_core/jenkins-analysis_memory_bank/**/*'
            }
        }
    }
}
```

## Documentation Platform Integration

### GitBook Integration

Script to convert memory bank to GitBook format:

```python
#!/usr/bin/env python3
"""Convert memory bank to GitBook structure."""

import os
import shutil
from pathlib import Path

def convert_to_gitbook(memory_bank_path: str, gitbook_path: str):
    """Convert memory bank to GitBook format."""
    memory_bank = Path(memory_bank_path) / "memory-bank"
    gitbook = Path(gitbook_path)
    
    # Create GitBook structure
    gitbook.mkdir(exist_ok=True)
    
    # Create SUMMARY.md
    summary_content = """# Summary

* [Project Overview](projectbrief.md)
* [Product Context](productContext.md)
* [System Architecture](systemPatterns.md)
* [Technology Stack](techContext.md)
* [Current State](activeContext.md)
* [Implementation Progress](progress.md)
* [Development Tasks](tasks/README.md)
"""
    
    with open(gitbook / "SUMMARY.md", "w") as f:
        f.write(summary_content)
    
    # Copy memory bank files
    for md_file in memory_bank.glob("*.md"):
        shutil.copy2(md_file, gitbook / md_file.name)
    
    # Copy tasks directory
    if (memory_bank / "tasks").exists():
        shutil.copytree(memory_bank / "tasks", gitbook / "tasks", dirs_exist_ok=True)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python convert_to_gitbook.py <memory_bank_path> <gitbook_path>")
        sys.exit(1)
    
    convert_to_gitbook(sys.argv[1], sys.argv[2])
    print("Conversion complete!")
```

### Notion Integration

Script to upload memory bank to Notion:

```python
#!/usr/bin/env python3
"""Upload memory bank to Notion."""

import os
from pathlib import Path
from notion_client import Client

def upload_to_notion(memory_bank_path: str, notion_token: str, database_id: str):
    """Upload memory bank content to Notion database."""
    notion = Client(auth=notion_token)
    memory_bank = Path(memory_bank_path) / "memory-bank"
    
    # Create parent page
    parent_page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"title": [{"text": {"content": f"Memory Bank - {memory_bank_path}"}}]},
            "Type": {"select": {"name": "Memory Bank"}},
        }
    )
    
    # Upload each markdown file as a child page
    for md_file in memory_bank.glob("*.md"):
        with open(md_file, "r") as f:
            content = f.read()
        
        notion.pages.create(
            parent={"page_id": parent_page["id"]},
            properties={
                "Name": {"title": [{"text": {"content": md_file.stem.title()}}]}
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
                    }
                }
            ]
        )

if __name__ == "__main__":
    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_DATABASE_ID")
    
    if not token or not db_id:
        print("Set NOTION_TOKEN and NOTION_DATABASE_ID environment variables")
        sys.exit(1)
    
    import sys
    if len(sys.argv) != 2:
        print("Usage: python upload_to_notion.py <memory_bank_path>")
        sys.exit(1)
    
    upload_to_notion(sys.argv[1], token, db_id)
```

## IDE Integration

### VS Code Extension Concept

Create a simple VS Code task in `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Generate Memory Bank",
            "type": "shell",
            "command": "uv",
            "args": [
                "run", "python", "-m", "memory_bank_core", 
                "build", "${workspaceFolder}", 
                "--output-name", "${workspaceFolderBasename}-analysis"
            ],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "options": {
                "cwd": "${workspaceFolder}/../memory-bank-builder/memory_bank_core"
            },
            "problemMatcher": []
        }
    ]
}
```

## Automated Workflows

### Daily Analysis Cron Job

```bash
#!/bin/bash
# daily-analysis.sh

# Configuration
PROJECTS_DIR="/home/user/projects"
OUTPUT_DIR="/home/user/memory-banks"
LOG_FILE="/var/log/memory-bank-daily.log"

echo "$(date): Starting daily memory bank analysis" >> $LOG_FILE

# Analyze each project
for project in "$PROJECTS_DIR"/*; do
    if [ -d "$project" ]; then
        project_name=$(basename "$project")
        echo "Analyzing $project_name..." >> $LOG_FILE
        
        cd /path/to/memory-bank-builder/memory_bank_core
        uv run python -m memory_bank_core build "$project" \
            --root-path "$OUTPUT_DIR" \
            --output-name "$project_name-$(date +%Y%m%d)" \
            --no-wait
    fi
done

echo "$(date): Daily analysis complete" >> $LOG_FILE
```

Add to crontab:
```bash
# Run daily at 2 AM
0 2 * * * /path/to/daily-analysis.sh
```

### Slack Integration

Post memory bank summaries to Slack:

```python
#!/usr/bin/env python3
"""Post memory bank summary to Slack."""

import json
import requests
from pathlib import Path

def post_to_slack(memory_bank_path: str, webhook_url: str):
    """Post memory bank summary to Slack."""
    memory_bank = Path(memory_bank_path)
    
    # Read project brief
    brief_file = memory_bank / "memory-bank" / "projectbrief.md"
    if brief_file.exists():
        with open(brief_file, "r") as f:
            brief = f.read()[:500] + "..."
    else:
        brief = "Memory bank generated successfully"
    
    # Create Slack message
    message = {
        "text": "🧠 Memory Bank Generated",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🧠 Memory Bank Analysis Complete"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Project:* {memory_bank.name}\n*Analysis:*\n```{brief}```"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Analysis"},
                        "url": f"file://{memory_bank.absolute()}"
                    }
                ]
            }
        ]
    }
    
    response = requests.post(webhook_url, json=message)
    return response.status_code == 200

if __name__ == "__main__":
    import sys, os
    
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        print("Set SLACK_WEBHOOK_URL environment variable")
        sys.exit(1)
    
    if len(sys.argv) != 2:
        print("Usage: python slack_notify.py <memory_bank_path>")
        sys.exit(1)
    
    success = post_to_slack(sys.argv[1], webhook)
    print("Slack notification sent!" if success else "Failed to send notification")
```

## Performance Optimization

### Batch Processing

```bash
#!/bin/bash
# batch-process.sh - Process multiple repositories efficiently

# Start worker in background
uv run python -m memory_bank_core worker --max-jobs 3 &
WORKER_PID=$!

# Queue multiple jobs
for repo in /path/to/repos/*; do
    if [ -d "$repo" ]; then
        echo "Queuing $(basename "$repo")..."
        uv run python -m memory_bank_core build "$repo" --no-wait
    fi
done

# Wait for processing to complete
echo "Waiting for all jobs to complete..."
wait $WORKER_PID
```

### Incremental Updates

```bash
#!/bin/bash
# incremental-update.sh - Smart incremental updates

PROJECT_PATH="/path/to/project"
MEMORY_BANK="project-analysis"
LAST_UPDATE_FILE=".last-memory-bank-update"

# Check if project changed since last update
if [ -f "$LAST_UPDATE_FILE" ]; then
    CHANGED_FILES=$(git diff --name-only HEAD $(cat $LAST_UPDATE_FILE) | wc -l)
    if [ $CHANGED_FILES -eq 0 ]; then
        echo "No changes since last update. Skipping..."
        exit 0
    fi
fi

# Update memory bank
echo "Updating memory bank (detected $CHANGED_FILES changed files)..."
uv run python -m memory_bank_core update "$PROJECT_PATH" "$MEMORY_BANK"

# Record update
git rev-parse HEAD > "$LAST_UPDATE_FILE"
```

## Best Practices

### 1. Environment Management
- Use separate API keys for different environments
- Set appropriate rate limits for CI/CD
- Cache memory bank builder installation

### 2. Security
- Store API keys securely (GitHub Secrets, etc.)
- Don't commit generated memory banks to version control
- Use appropriate file permissions for output directories

### 3. Performance
- Use worker mode for multiple projects
- Implement incremental updates where possible
- Monitor API usage and costs

### 4. Documentation
- Include memory bank generation in your project documentation
- Set up automated documentation updates
- Train team members on memory bank interpretation

These integrations help make MemBankBuilder a seamless part of your development workflow, providing continuous insights into your codebase evolution.