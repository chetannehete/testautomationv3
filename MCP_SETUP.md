# MD Agent MCP Server Setup Guide

## Overview

MD Agent is now available as an MCP (Model Context Protocol) server, allowing AI assistants and other MCP clients to generate Java test cases and documentation programmatically.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

### 1. Install Dependencies

```bash
cd "c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test automation"
pip install -r requirements.txt
```

This will install:
- `javalang` - Java source code parser
- `Jinja2` - Template engine for Markdown generation
- `click` - CLI framework
- `mcp` - Model Context Protocol SDK

### 2. Verify Installation

Test that the MCP server can start:

```bash
python -m md_agent.mcp_server
```

The server should start and wait for MCP protocol messages on stdin/stdout.

## Configuration

### Claude Desktop

1. **Locate the Claude Desktop configuration file:**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add the MD Agent server configuration:**

```json
{
  "mcpServers": {
    "md-agent": {
      "command": "python",
      "args": ["-m", "md_agent.mcp_server"],
      "cwd": "c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test automation"
    }
  }
}
```

3. **Restart Claude Desktop**

### Other MCP Clients

Copy the configuration from `mcp_config.json` and adapt the `cwd` path to your installation directory.

## Available Tools

### 1. `generate_test_cases`

Generate comprehensive test cases from Java source code.

**Parameters:**
- `source_code` (string, optional): Raw Java source code
- `file_path` (string, optional): Path to Java source file
- `output_format` (string): "markdown" or "json" (default: "markdown")

**Example:**

```json
{
  "file_path": "samples/Calculator.java",
  "output_format": "markdown"
}
```

**Output:**
- Markdown format: Formatted test case table with TC IDs, categories, descriptions, steps, and expected results
- JSON format: Structured test case data with all fields

### 2. `generate_documentation`

Generate comprehensive documentation from Java source code.

**Parameters:**
- `source_code` (string, optional): Raw Java source code
- `file_path` (string, optional): Path to Java source file
- `output_format` (string): "markdown" or "json" (default: "markdown")

**Example:**

```json
{
  "source_code": "public class Example { ... }",
  "output_format": "json"
}
```

**Output:**
- Markdown format: Formatted documentation with class overview, fields, methods, and Javadoc
- JSON format: Structured documentation data

### 3. `generate_both`

Generate both test cases and documentation in a single call.

**Parameters:**
- `source_code` (string, optional): Raw Java source code
- `file_path` (string, optional): Path to Java source file
- `output_format` (string): "markdown" or "json" (default: "markdown")

**Example:**

```json
{
  "file_path": "samples/Calculator.java",
  "output_format": "markdown"
}
```

## Usage Examples

### Using with Claude Desktop

Once configured, you can ask Claude to use the MD Agent tools:

> "Use the generate_test_cases tool to create test cases for the Calculator.java file in samples/"

> "Generate documentation for this Java class: [paste code]"

> "Use generate_both to create test cases and docs for samples/Calculator.java"

### Programmatic Usage

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_md_agent():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "md_agent.mcp_server"],
        cwd="c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test automation"
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call generate_test_cases
            result = await session.call_tool(
                "generate_test_cases",
                arguments={
                    "file_path": "samples/Calculator.java",
                    "output_format": "json"
                }
            )
            print(result)

asyncio.run(use_md_agent())
```

## Troubleshooting

### Server doesn't start

**Issue:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Tools not appearing in Claude Desktop

**Issue:** MD Agent tools don't show up in Claude

**Solution:**
1. Check that `claude_desktop_config.json` is correctly formatted
2. Verify the `cwd` path is correct and absolute
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

### Permission errors

**Issue:** `PermissionError` when accessing files

**Solution:** Ensure the `cwd` path in the configuration has proper read permissions

### Unicode encoding errors on Windows

**Issue:** `UnicodeEncodeError` when running the server

**Solution:** Set the UTF-8 environment variable:
```powershell
$env:PYTHONUTF8=1
python -m md_agent.mcp_server
```

Or add to the MCP config:
```json
{
  "mcpServers": {
    "md-agent": {
      "command": "python",
      "args": ["-m", "md_agent.mcp_server"],
      "cwd": "c:/Users/cheta/OneDrive/Desktop/aNTIGRAVITY/test automation",
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

## CLI Still Available

The original CLI interface remains fully functional:

```bash
# Generate test cases
python -m md_agent testcases samples/Calculator.java

# Generate documentation
python -m md_agent docs samples/Calculator.java

# Generate both
python -m md_agent generate samples/Calculator.java
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the MCP protocol logs
3. Test the CLI interface to isolate MCP-specific issues
