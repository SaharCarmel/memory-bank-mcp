#!/usr/bin/env python3
"""
MCP Server for PC Cortex Memory Banks

This server provides tools for LLMs to interact with memory banks:
1. List all available memory banks
2. Get files for a specific memory bank
3. Query and retrieve relevant files with their content
"""

from fastmcp import FastMCP
import httpx
from typing import List, Dict, Any, Optional
import os

# Initialize the MCP server
mcp = FastMCP("PC Cortex Memory Bank Server")

# Backend API configuration
BACKEND_URL = os.getenv("PC_CORTEX_BACKEND_URL", "http://localhost:8888")
API_PREFIX = "/api"


def make_api_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make a request to the backend API"""
    url = f"{BACKEND_URL}{API_PREFIX}{endpoint}"
    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise Exception(f"API request failed: {str(e)}")


@mcp.tool()
def list_memory_banks() -> List[Dict[str, Any]]:
    """
    List all available memory banks in the system.
    
    Returns a list of memory bank summaries including:
    - name: The name of the memory bank
    - path: The file system path
    - file_count: Number of files in the memory bank
    - task_count: Number of tasks
    - last_updated: When it was last updated
    - has_changelog: Whether it has a changelog
    """
    return make_api_request("/memory-banks")


@mcp.tool()
def get_memory_bank_files(memory_bank_name: str) -> List[str]:
    """
    Get the list of all files in a specific memory bank.
    
    Args:
        memory_bank_name: The name of the memory bank to query
        
    Returns:
        A list of file names in the memory bank
    """
    result = make_api_request(f"/memory-banks/{memory_bank_name}/files")
    return result.get("files", [])


@mcp.tool()
def get_memory_bank_file_content(memory_bank_name: str, filename: str) -> Dict[str, str]:
    """
    Get the content of a specific file from a memory bank.
    
    Args:
        memory_bank_name: The name of the memory bank
        filename: The name of the file to retrieve
        
    Returns:
        A dictionary with:
        - filename: The name of the file
        - content: The full content of the file
    """
    return make_api_request(f"/memory-banks/{memory_bank_name}/files/{filename}")


@mcp.tool()
def get_memory_bank_details(memory_bank_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific memory bank.
    
    Args:
        memory_bank_name: The name of the memory bank
        
    Returns:
        Detailed memory bank information including:
        - Basic info (name, path, timestamps)
        - All files with their metadata
        - Tasks
        - Changelog entries
        - Generation summary
        - Graph data if available
    """
    return make_api_request(f"/memory-banks/{memory_bank_name}")


@mcp.tool()
def query_memory_bank_files(
    memory_bank_name: str,
    file_patterns: List[str],
    include_content: bool = True
) -> List[Dict[str, Any]]:
    """
    Query specific files from a memory bank based on patterns.
    This is useful when you want to retrieve multiple specific files at once.
    
    Args:
        memory_bank_name: The name of the memory bank
        file_patterns: List of file name patterns to match (e.g., ["*.py", "README.md"])
        include_content: Whether to include file content in the response (default: True)
        
    Returns:
        A list of matching files with their content (if requested)
    """
    # First get all files
    all_files = get_memory_bank_files(memory_bank_name)
    
    # Filter files based on patterns
    matching_files = []
    for pattern in file_patterns:
        if "*" in pattern:
            # Simple wildcard matching
            prefix = pattern.replace("*", "")
            matching_files.extend([f for f in all_files if f.startswith(prefix) or f.endswith(prefix)])
        else:
            # Exact match
            if pattern in all_files:
                matching_files.append(pattern)
    
    # Remove duplicates
    matching_files = list(set(matching_files))
    
    # Get content if requested
    result = []
    for filename in matching_files:
        file_info = {"filename": filename}
        if include_content:
            content_response = get_memory_bank_file_content(memory_bank_name, filename)
            file_info["content"] = content_response.get("content", "")
        result.append(file_info)
    
    return result


@mcp.tool()
def search_memory_bank_content(
    memory_bank_name: str,
    search_term: str,
    case_sensitive: bool = False
) -> List[Dict[str, Any]]:
    """
    Search for content within a memory bank's files.
    
    Args:
        memory_bank_name: The name of the memory bank to search
        search_term: The term to search for in file contents
        case_sensitive: Whether the search should be case-sensitive (default: False)
        
    Returns:
        A list of files containing the search term with matching excerpts
    """
    # Get all files
    files = get_memory_bank_files(memory_bank_name)
    
    results = []
    search_lower = search_term.lower() if not case_sensitive else search_term
    
    for filename in files:
        try:
            content_response = get_memory_bank_file_content(memory_bank_name, filename)
            content = content_response.get("content", "")
            
            # Search in content
            content_to_search = content if case_sensitive else content.lower()
            if search_lower in content_to_search:
                # Find line numbers with matches
                lines = content.split("\n")
                matching_lines = []
                
                for i, line in enumerate(lines, 1):
                    line_to_search = line if case_sensitive else line.lower()
                    if search_lower in line_to_search:
                        matching_lines.append({
                            "line_number": i,
                            "line": line.strip()
                        })
                
                results.append({
                    "filename": filename,
                    "match_count": len(matching_lines),
                    "matching_lines": matching_lines[:5]  # Limit to first 5 matches
                })
        except Exception:
            # Skip files that can't be read
            continue
    
    return results


# Add a resource that provides server information
@mcp.resource("pc-cortex://server-info")
async def get_server_info() -> str:
    """Information about the PC Cortex MCP Server"""
    return f"""
# PC Cortex Memory Bank MCP Server

This server provides access to memory banks in the PC Cortex system.

## Available Tools:

1. **list_memory_banks()** - List all available memory banks
2. **get_memory_bank_files(memory_bank_name)** - Get files in a specific memory bank
3. **get_memory_bank_file_content(memory_bank_name, filename)** - Get content of a specific file
4. **get_memory_bank_details(memory_bank_name)** - Get detailed information about a memory bank
5. **query_memory_bank_files(memory_bank_name, file_patterns, include_content)** - Query specific files by pattern
6. **search_memory_bank_content(memory_bank_name, search_term, case_sensitive)** - Search content within files

## Configuration:

Backend URL: {BACKEND_URL}

## Usage Example:

1. First, list available memory banks:
   ```
   list_memory_banks()
   ```

2. Then get files from a specific memory bank:
   ```
   get_memory_bank_files("my_project")
   ```

3. Retrieve specific file content:
   ```
   get_memory_bank_file_content("my_project", "README.md")
   ```
"""


if __name__ == "__main__":
    # Run the server
    mcp.run()