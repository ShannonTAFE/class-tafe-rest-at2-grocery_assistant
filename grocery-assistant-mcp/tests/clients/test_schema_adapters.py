from clients.shared.mcp_helpers import MCPToolInfo
from clients.shared.schema_adapters import to_openai_chat_tool, to_openai_chat_tools


def test_to_openai_chat_tool_shape():
    tool = MCPToolInfo(
        name="search_inventory",
        description="Search inventory",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )

    result = to_openai_chat_tool(tool)

    assert result["type"] == "function"
    assert result["function"]["name"] == "search_inventory"
    assert result["function"]["description"] == "Search inventory"
    assert result["function"]["parameters"]["type"] == "object"


def test_to_openai_chat_tools_list():
    tools = [
        MCPToolInfo("search_inventory", "Search", {"type": "object"}),
        MCPToolInfo("review_low_stock_items", "Review", {"type": "object"}),
    ]

    result = to_openai_chat_tools(tools)

    assert [item["function"]["name"] for item in result] == [
        "search_inventory",
        "review_low_stock_items",
    ]
