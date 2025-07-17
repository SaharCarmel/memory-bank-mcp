#!/bin/bash

# Memory Bank Updater Script
# Usage: ./update_memory_bank.sh [repo_path] [memory_bank_path] [options]

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
REPO_PATH="${1:-.}"
MEMORY_BANK_PATH="${2}"

echo -e "${BLUE}=== Memory Bank Updater ===${NC}"
echo -e "Repository: ${GREEN}$REPO_PATH${NC}"
echo -e "Memory Bank: ${GREEN}$MEMORY_BANK_PATH${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed${NC}"
    exit 1
fi

# Check if the repo path exists
if [ ! -d "$REPO_PATH" ]; then
    echo -e "${RED}Error: Repository path does not exist: $REPO_PATH${NC}"
    exit 1
fi

# Check if memory bank path is provided
if [ -z "$MEMORY_BANK_PATH" ]; then
    echo -e "${RED}Error: Memory bank path is required${NC}"
    echo "Usage: $0 <repo_path> <memory_bank_path>"
    exit 1
fi

# Check if memory bank exists
if [ ! -d "$MEMORY_BANK_PATH" ]; then
    echo -e "${RED}Error: Memory bank path does not exist: $MEMORY_BANK_PATH${NC}"
    echo "Run the memory bank builder first to create the initial memory bank"
    exit 1
fi

echo -e "${BLUE}Getting git changes...${NC}"

# Get git diff from various sources
if [ "$3" = "--stdin" ]; then
    echo -e "${GREEN}Reading diff from stdin...${NC}"
    uv run python3 update_memory_bank.py "$REPO_PATH" "$MEMORY_BANK_PATH" --diff-stdin -v
elif [ "$3" = "--since-commit" ] && [ -n "$4" ]; then
    echo -e "${GREEN}Getting diff since commit $4...${NC}"
    uv run python3 update_memory_bank.py "$REPO_PATH" "$MEMORY_BANK_PATH" --since-commit "$4" -v
elif [ -n "$3" ] && [ -f "$3" ]; then
    echo -e "${GREEN}Reading diff from file $3...${NC}"
    uv run python3 update_memory_bank.py "$REPO_PATH" "$MEMORY_BANK_PATH" --diff-file "$3" -v
else
    # Default: get diff from last commit
    echo -e "${GREEN}Getting diff from last commit...${NC}"
    uv run python3 update_memory_bank.py "$REPO_PATH" "$MEMORY_BANK_PATH" --since-commit "HEAD~1" -v
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Memory bank updated successfully!${NC}"
else
    echo -e "${RED}❌ Memory bank update failed!${NC}"
    exit 1
fi