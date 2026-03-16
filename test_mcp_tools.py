"""
Simple test script to verify MCP tools functionality.
"""

from md_agent.mcp_tools import (
    generate_test_cases_tool,
    generate_documentation_tool,
    generate_both_tool,
)

# Test with Calculator.java file
print("=" * 60)
print("Testing generate_test_cases_tool with file_path...")
print("=" * 60)

result = generate_test_cases_tool(
    file_path="samples/Calculator.java",
    output_format="json"
)

if result["success"]:
    print(f"[OK] Success! Generated {len(result['data'])} class(es)")
    for cls_data in result['data']:
        print(f"  - {cls_data['class_name']}: {len(cls_data['test_cases'])} test cases")
else:
    print(f"[ERROR] Error: {result['error']}")

print("\n" + "=" * 60)
print("Testing generate_documentation_tool with file_path...")
print("=" * 60)

result = generate_documentation_tool(
    file_path="samples/Calculator.java",
    output_format="json"
)

if result["success"]:
    print(f"[OK] Success! Generated {len(result['data'])} class(es)")
    for cls_data in result['data']:
        print(f"  - {cls_data['class_name']}: {len(cls_data['sections'])} sections")
else:
    print(f"[ERROR] Error: {result['error']}")

print("\n" + "=" * 60)
print("Testing generate_both_tool with source_code...")
print("=" * 60)

sample_code = """
package com.example;

public class Sample {
    public int add(int a, int b) {
        return a + b;
    }
}
"""

result = generate_both_tool(
    source_code=sample_code,
    output_format="markdown"
)

if result["success"]:
    print(f"[OK] Success!")
    print(f"  - Test cases: {len(result['test_cases'])} class(es)")
    print(f"  - Documentation: {len(result['documentation'])} class(es)")
    if result['test_cases']:
        print(f"\n  Sample test case markdown (first 200 chars):")
        print(f"  {result['test_cases'][0]['markdown'][:200]}...")
else:
    print(f"[ERROR] Error: {result['error']}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)

