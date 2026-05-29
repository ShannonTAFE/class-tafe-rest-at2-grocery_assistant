from dataclasses import dataclass

import pytest

from clients.shared.mcp_helpers import (
    compact_tool_result,
    filter_mcp_tools,
    tool_info_from_mcp_tool,
)


@dataclass
class FakeTool:
    name: str
    description: str
    inputSchema: dict


class FakeResult:
    def __init__(self, structured_content):
        self.structured_content = structured_content


def test_tool_info_from_mcp_tool_normalises_schema():
    tool = FakeTool(
        name="search_inventory",
        description="Search inventory",
        inputSchema={"type": "object", "properties": {"query": {"type": "string"}}},
    )

    info = tool_info_from_mcp_tool(tool)

    assert info.name == "search_inventory"
    assert info.description == "Search inventory"
    assert info.input_schema["type"] == "object"
    assert "properties" in info.input_schema
    assert "required" in info.input_schema


def test_filter_mcp_tools_uses_policy():
    tools = [
        FakeTool("search_inventory", "Search", {"type": "object"}),
        FakeTool("add_inventory_item", "Add", {"type": "object"}),
        FakeTool("unknown_tool", "Unknown", {"type": "object"}),
    ]

    assert [tool.name for tool in filter_mcp_tools(tools, allow_writes=False)] == [
        "search_inventory"
    ]
    assert [tool.name for tool in filter_mcp_tools(tools, allow_writes=True)] == [
        "search_inventory",
        "add_inventory_item",
    ]


def test_compact_tool_result_prefers_structured_content():
    result = FakeResult({"result": [{"food_item": "Rice"}]})

    text = compact_tool_result(result)

    assert '"food_item": "Rice"' in text


def test_compact_tool_result_truncates():
    result = FakeResult({"result": "x" * 100})

    text = compact_tool_result(result, max_chars=20)

    assert text.endswith("... [tool result truncated]")
