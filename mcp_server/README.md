# PC Cortex MCP Server

This MCP (Model Context Protocol) server provides tools for LLMs to interact with PC Cortex memory banks through the backend API.

## Features

The server provides the following tools:

1. **list_memory_banks()** - List all available memory banks
2. **get_memory_bank_files(memory_bank_name)** - Get all files in a specific memory bank
3. **get_memory_bank_file_content(memory_bank_name, filename)** - Get the content of a specific file
4. **get_memory_bank_details(memory_bank_name)** - Get detailed information about a memory bank
5. **query_memory_bank_files(memory_bank_name, file_patterns, include_content)** - Query files by pattern
6. **search_memory_bank_content(memory_bank_name, search_term, case_sensitive)** - Search within file contents

## Prerequisites

1. Make sure the PC Cortex backend is running on http://localhost:8888
2. Install UV package manager if not already installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Installation

1. Navigate to the mcp_server directory:
   ```bash
   cd mcp_server
   ```

2. Install dependencies (already done):
   ```bash
   uv add fastmcp httpx
   ```

## Running the Server

### Standalone Mode (for testing)

```bash
uv run python server.py
```

You can then test it using the MCP Inspector:
```bash
uv run mcp dev server.py
```

### Configure with Claude Desktop

1. Copy the configuration to Claude Desktop's config file:
   ```bash
   # On macOS
   cp claude_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   Or manually merge the configuration if you already have other MCP servers configured.

2. Restart Claude Desktop

3. The PC Cortex tools should now be available in Claude

## Environment Variables

- `PC_CORTEX_BACKEND_URL`: URL of the PC Cortex backend (default: http://localhost:8888)

## Usage Example in Claude

Once configured, you can use commands like:

```
Use the PC Cortex tools to:
1. Show me all available memory banks
2. Get the files from the "my_project" memory bank
3. Show me the content of README.md from that memory bank
```

## Troubleshooting

1. **Backend Connection Error**: Make sure the PC Cortex backend is running on the specified URL
2. **Tools Not Available in Claude**: Ensure the configuration is properly added to claude_desktop_config.json and Claude Desktop has been restarted
3. **Permission Errors**: Make sure the server.py file has execute permissions:
   ```bash
   chmod +x server.py
   ```