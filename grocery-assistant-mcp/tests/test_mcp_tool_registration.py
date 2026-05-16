from grocery_assistant_mcp.stdio_server import create_mcp_server


def test_v1_1_inventory_tools_are_registered():
    mcp = create_mcp_server()

    tool_names = {tool.name for tool in mcp._tool_manager._tools.values()}

    expected_tools = {
        "search_inventory",
        "add_inventory_item",
        "update_inventory_item",
        "remove_inventory_item",
    }

    assert expected_tools.issubset(tool_names)


def test_v1_1_intake_tools_are_registered():
    mcp = create_mcp_server()

    tool_names = {tool.name for tool in mcp._tool_manager._tools.values()}

    expected_tools = {
        "get_recent_intake",
        "get_daily_intake_summary",
        "add_intake_entry",
        "add_intake_item",
    }

    assert expected_tools.issubset(tool_names)