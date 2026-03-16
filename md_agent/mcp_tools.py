"""
MCP tool implementations for MD Agent.

Provides wrapper functions that integrate the existing Java parser,
analyzer, and renderer modules with the MCP protocol.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from md_agent.java_parser import parse_java_file, parse_java_source
from md_agent.analyzer import generate_test_suite, generate_documentation
from md_agent.md_renderer import render_test_cases, render_documentation
from md_agent.models import TestSuite, Documentation, TestCase, DocSection


def _serialize_test_suite(suite: TestSuite) -> Dict[str, Any]:
    """Convert TestSuite to JSON-serializable dict."""
    return {
        "class_name": suite.class_name,
        "package": suite.package,
        "source_file": suite.source_file,
        "test_cases": [
            {
                "id": tc.id,
                "method_name": tc.method_name,
                "category": tc.category,
                "description": tc.description,
                "preconditions": tc.preconditions,
                "steps": tc.steps,
                "expected_result": tc.expected_result,
            }
            for tc in suite.test_cases
        ],
    }


def _serialize_documentation(doc: Documentation) -> Dict[str, Any]:
    """Convert Documentation to JSON-serializable dict."""
    return {
        "class_name": doc.class_info.name,
        "package": doc.class_info.package,
        "source_file": doc.class_info.source_file,
        "sections": [
            {
                "title": section.title,
                "content": section.content,
                "code_example": section.code_example,
                "level": section.level,
            }
            for section in doc.sections
        ],
    }


def generate_test_cases_tool(
    source_code: Optional[str] = None,
    file_path: Optional[str] = None,
    output_format: str = "markdown",
) -> Dict[str, Any]:
    """
    Generate test cases from Java source code.

    Args:
        source_code: Raw Java source code string (optional)
        file_path: Path to Java source file (optional)
        output_format: Output format - "markdown" or "json" (default: "markdown")

    Returns:
        Dict with 'success', 'data' (test cases), and optional 'error' fields
    """
    try:
        # Validate inputs
        if not source_code and not file_path:
            return {
                "success": False,
                "error": "Either source_code or file_path must be provided",
            }

        if source_code and file_path:
            return {
                "success": False,
                "error": "Provide either source_code or file_path, not both",
            }

        # Parse Java source
        if file_path:
            classes = parse_java_file(file_path)
            source_file = file_path
        else:
            classes = parse_java_source(source_code, source_file="<input>")
            source_file = "<input>"

        if not classes:
            return {
                "success": False,
                "error": "No Java classes found in the provided source",
            }

        # Generate test suites for all classes
        results = []
        for cls in classes:
            suite = generate_test_suite(cls)

            if output_format == "json":
                results.append(_serialize_test_suite(suite))
            else:  # markdown
                # Render to markdown using Jinja2 template
                from jinja2 import Environment, FileSystemLoader
                template_dir = Path(__file__).parent / "templates"
                env = Environment(
                    loader=FileSystemLoader(str(template_dir)),
                    trim_blocks=True,
                    lstrip_blocks=True,
                )
                template = env.get_template("test_cases.md.j2")
                markdown = template.render(suite=suite)
                results.append({
                    "class_name": suite.class_name,
                    "markdown": markdown,
                    "test_count": len(suite.test_cases),
                })

        return {
            "success": True,
            "data": results,
            "format": output_format,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating test cases: {str(e)}",
        }


def generate_documentation_tool(
    source_code: Optional[str] = None,
    file_path: Optional[str] = None,
    output_format: str = "markdown",
) -> Dict[str, Any]:
    """
    Generate documentation from Java source code.

    Args:
        source_code: Raw Java source code string (optional)
        file_path: Path to Java source file (optional)
        output_format: Output format - "markdown" or "json" (default: "markdown")

    Returns:
        Dict with 'success', 'data' (documentation), and optional 'error' fields
    """
    try:
        # Validate inputs
        if not source_code and not file_path:
            return {
                "success": False,
                "error": "Either source_code or file_path must be provided",
            }

        if source_code and file_path:
            return {
                "success": False,
                "error": "Provide either source_code or file_path, not both",
            }

        # Parse Java source
        if file_path:
            classes = parse_java_file(file_path)
            source_file = file_path
        else:
            classes = parse_java_source(source_code, source_file="<input>")
            source_file = "<input>"

        if not classes:
            return {
                "success": False,
                "error": "No Java classes found in the provided source",
            }

        # Generate documentation for all classes
        results = []
        for cls in classes:
            doc = generate_documentation(cls)

            if output_format == "json":
                results.append(_serialize_documentation(doc))
            else:  # markdown
                # Render to markdown using Jinja2 template
                from jinja2 import Environment, FileSystemLoader
                template_dir = Path(__file__).parent / "templates"
                env = Environment(
                    loader=FileSystemLoader(str(template_dir)),
                    trim_blocks=True,
                    lstrip_blocks=True,
                )
                template = env.get_template("documentation.md.j2")
                markdown = template.render(doc=doc)
                results.append({
                    "class_name": doc.class_info.name,
                    "markdown": markdown,
                    "section_count": len(doc.sections),
                })

        return {
            "success": True,
            "data": results,
            "format": output_format,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating documentation: {str(e)}",
        }


def generate_both_tool(
    source_code: Optional[str] = None,
    file_path: Optional[str] = None,
    output_format: str = "markdown",
) -> Dict[str, Any]:
    """
    Generate both test cases and documentation from Java source code.

    Args:
        source_code: Raw Java source code string (optional)
        file_path: Path to Java source file (optional)
        output_format: Output format - "markdown" or "json" (default: "markdown")

    Returns:
        Dict with 'success', 'test_cases', 'documentation', and optional 'error' fields
    """
    try:
        # Generate test cases
        test_result = generate_test_cases_tool(
            source_code=source_code,
            file_path=file_path,
            output_format=output_format,
        )

        # Generate documentation
        doc_result = generate_documentation_tool(
            source_code=source_code,
            file_path=file_path,
            output_format=output_format,
        )

        # Check if both succeeded
        if not test_result["success"]:
            return test_result

        if not doc_result["success"]:
            return doc_result

        return {
            "success": True,
            "test_cases": test_result["data"],
            "documentation": doc_result["data"],
            "format": output_format,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating artifacts: {str(e)}",
        }
