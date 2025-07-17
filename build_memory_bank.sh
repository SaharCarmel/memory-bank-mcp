#!/bin/bash

# Memory Bank Builder Script
# Usage: ./build_memory_bank.sh [repo_path] [output_name]

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
REPO_PATH="${1:-.}"

# Generate default output name based on repo folder name
if [ -z "$2" ]; then
    REPO_NAME=$(basename "$REPO_PATH")
    OUTPUT_NAME="${REPO_NAME}_memory_bank"
else
    OUTPUT_NAME="$2"
fi

OUTPUT_PATH="./${OUTPUT_NAME}"

echo -e "${BLUE}=== Memory Bank Builder ===${NC}"
echo -e "Repository: ${GREEN}$REPO_PATH${NC}"
echo -e "Output: ${GREEN}$OUTPUT_PATH${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if the repo path exists
if [ ! -d "$REPO_PATH" ]; then
    echo -e "${RED}Error: Repository path does not exist: $REPO_PATH${NC}"
    exit 1
fi

# Clean up previous output if it exists
if [ -d "$OUTPUT_PATH" ]; then
    echo -e "${BLUE}Cleaning up previous output...${NC}"
    rm -rf "$OUTPUT_PATH"
fi

# Try different builders in order of preference
echo -e "${BLUE}Attempting to build memory bank...${NC}"

# 1. Try the writer version (lets Claude write files directly)
if [ -f "memory_bank_builder_writer.py" ] && command -v uv &> /dev/null; then
    echo -e "${GREEN}Using writer version (Claude writes files directly)...${NC}"
    uv run python3 memory_bank_builder_writer.py "$REPO_PATH" -o "$OUTPUT_PATH" -v
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Memory bank built successfully!${NC}"
        echo -e "Output saved to: ${BLUE}$OUTPUT_PATH${NC}"
        exit 0
    fi
fi

# 2. Try the standalone version
if [ -f "pc_cortex" ]; then
    echo -e "${GREEN}Using standalone version...${NC}"
    ./pc_cortex "$REPO_PATH" -o "$OUTPUT_PATH" -v
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Memory bank built successfully!${NC}"
        echo -e "Output saved to: ${BLUE}$OUTPUT_PATH${NC}"
        exit 0
    fi
fi

echo -e "${RED}Error: No memory bank builder found${NC}"
exit 1