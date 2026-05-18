from grocery_assistant_mcp.stdio_server import create_mcp_server


def get_registered_tool_names() -> set[str]:
    mcp = create_mcp_server()
    return {tool.name for tool in mcp._tool_manager._tools.values()}


def test_v1_1_inventory_tools_are_registered():
    tool_names = get_registered_tool_names()

    expected_tools = {
        "search_inventory",
        "add_inventory_item",
        "update_inventory_item",
        "remove_inventory_item",
    }

    assert expected_tools.issubset(tool_names)


def test_v1_1_intake_tools_are_registered():
    tool_names = get_registered_tool_names()

    expected_tools = {
        "get_recent_intake",
        "get_daily_intake_summary",
        "add_intake_entry",
        "add_intake_item",
    }

    assert expected_tools.issubset(tool_names)


def test_v1_3_consumption_tools_are_registered():
    tool_names = get_registered_tool_names()

    expected_tools = {
        "consume_inventory_item",
        "add_intake_item_from_inventory",
    }

    assert expected_tools.issubset(tool_names)


def test_expected_mcp_tools_are_registered():
    tool_names = get_registered_tool_names()

    expected_tools = {
        # Inventory tools
        "search_inventory",
        "add_inventory_item",
        "update_inventory_item",
        "remove_inventory_item",

        # Intake read/search tools
        "get_recent_intake",
        "get_daily_intake_summary",
        "search_intake",

        # Intake write tools
        "add_intake_entry",
        "add_intake_item",
        "update_intake_entry",
        "update_intake_item",
        "remove_intake_item",
        "remove_intake_entry",

        # Version 1.3 controlled consumption tools
        "consume_inventory_item",
        "add_intake_item_from_inventory",
    }

    missing_tools = expected_tools - tool_names

    assert not missing_tools, f"Missing MCP tools: {missing_tools}"

def test_add_meal_with_items_tool_is_registered():
    mcp = create_mcp_server()

    tool_names = {
        tool.name
        for tool in mcp._tool_manager.list_tools()
    }

    assert "add_meal_with_items" in tool_names

def test_batch_meal_tools_are_registered():
    mcp = create_mcp_server()

    tool_names = {
        tool.name
        for tool in mcp._tool_manager.list_tools()
    }

    assert "add_meal_with_items" in tool_names
    assert "add_meal_with_inventory_items" in tool_names