"""
MCP Server for MD Agent.

Exposes Java test case and documentation generation tools via the MCP protocol.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from md_agent.mcp_tools import (
    generate_test_cases_tool,
    generate_documentation_tool,
    generate_both_tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("md_agent.mcp_server")

# Initialize MCP server
app = Server("md-agent")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="generate_test_cases",
            description=(
                "Generate comprehensive test cases from Java source code. "
                "Analyzes methods and generates test cases for happy path, "
                "boundary conditions, edge cases, and exception scenarios. "
                "Supports both file paths and raw source code input."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source_code": {
                        "type": "string",
                        "description": "Raw Java source code (optional, use this OR file_path)",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to Java source file (optional, use this OR source_code)",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "default": "markdown",
                        "description": "Output format: 'markdown' for formatted text or 'json' for structured data",
                    },
                },
                "oneOf": [
                    {"required": ["source_code"]},
                    {"required": ["file_path"]},
                ],
            },
        ),
        Tool(
            name="generate_documentation",
            description=(
                "Generate comprehensive documentation from Java source code. "
                "Creates structured documentation including class overview, "
                "fields, methods, parameters, return types, and Javadoc comments. "
                "Supports both file paths and raw source code input."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source_code": {
                        "type": "string",
                        "description": "Raw Java source code (optional, use this OR file_path)",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to Java source file (optional, use this OR source_code)",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "default": "markdown",
                        "description": "Output format: 'markdown' for formatted text or 'json' for structured data",
                    },
                },
                "oneOf": [
                    {"required": ["source_code"]},
                    {"required": ["file_path"]},
                ],
            },
        ),
        Tool(
            name="generate_both",
            description=(
                "Generate both test cases and documentation from Java source code. "
                "Combines the functionality of generate_test_cases and generate_documentation "
                "for comprehensive analysis. Supports both file paths and raw source code input."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source_code": {
                        "type": "string",
                        "description": "Raw Java source code (optional, use this OR file_path)",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to Java source file (optional, use this OR source_code)",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "default": "markdown",
                        "description": "Output format: 'markdown' for formatted text or 'json' for structured data",
                    },
                },
                "oneOf": [
                    {"required": ["source_code"]},
                    {"required": ["file_path"]},
                ],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool invocations."""
    try:
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {arguments}")

        # Extract arguments
        source_code = arguments.get("source_code")
        file_path = arguments.get("file_path")
        output_format = arguments.get("output_format", "markdown")

        # Route to appropriate tool
        if name == "generate_test_cases":
            result = generate_test_cases_tool(
                source_code=source_code,
                file_path=file_path,
                output_format=output_format,
            )
        elif name == "generate_documentation":
            result = generate_documentation_tool(
                source_code=source_code,
                file_path=file_path,
                output_format=output_format,
            )
        elif name == "generate_both":
            result = generate_both_tool(
                source_code=source_code,
                file_path=file_path,
                output_format=output_format,
            )
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

        # Format response
        if result["success"]:
            import json
            response_text = json.dumps(result, indent=2)
        else:
            response_text = f"Error: {result.get('error', 'Unknown error')}"

        return [
            TextContent(
                type="text",
                text=response_text,
            )
        ]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=f"Error executing tool: {str(e)}",
            )
        ]


async def main():
    """Run the MCP server."""
    logger.info("Starting MD Agent MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
