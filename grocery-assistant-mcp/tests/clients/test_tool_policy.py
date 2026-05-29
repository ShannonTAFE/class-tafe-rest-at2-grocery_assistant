from clients.shared.tool_policy import (
    READ_REVIEW_DRAFT_TOOLS,
    WRITE_TOOLS,
    allowed_tool_names,
    filter_tool_names,
    is_destructive_tool,
    is_tool_allowed,
    is_write_tool,
    merge_default_args,
)


def test_default_allowed_tools_are_read_review_draft_only():
    allowed = allowed_tool_names(allow_writes=False)

    assert "search_inventory" in allowed
    assert "review_planning_context" in allowed
    assert "draft_meal_suggestions_tool" in allowed
    assert "add_inventory_item" not in allowed
    assert "remove_inventory_item" not in allowed


def test_write_mode_adds_write_tools():
    allowed = allowed_tool_names(allow_writes=True)

    assert READ_REVIEW_DRAFT_TOOLS <= allowed
    assert WRITE_TOOLS <= allowed
    assert "add_inventory_item" in allowed
    assert "add_meal_with_inventory_items" in allowed


def test_tool_classification():
    assert is_write_tool("add_inventory_item")
    assert is_write_tool("consume_inventory_item")
    assert not is_write_tool("review_low_stock_items")

    assert is_destructive_tool("remove_inventory_item")
    assert not is_destructive_tool("consume_inventory_item")


def test_is_tool_allowed_hides_unknown_tools():
    assert is_tool_allowed("search_inventory", allow_writes=False)
    assert not is_tool_allowed("add_inventory_item", allow_writes=False)
    assert not is_tool_allowed("unknown_future_tool", allow_writes=True)


def test_filter_tool_names_preserves_server_order():
    names = ["add_inventory_item", "search_inventory", "review_planning_context", "unknown"]

    assert filter_tool_names(names, allow_writes=False) == [
        "search_inventory",
        "review_planning_context",
    ]
    assert filter_tool_names(names, allow_writes=True) == [
        "add_inventory_item",
        "search_inventory",
        "review_planning_context",
    ]


def test_merge_default_args_fills_known_defaults():
    assert merge_default_args("search_inventory", {"query": "rice"}) == {
        "query": "rice",
        "category": "",
        "location": "",
    }

    assert merge_default_args("review_use_soon_items", {}) == {
        "include_use_soon": True,
        "include_expired": True,
        "include_no_expiry_data": True,
        "include_invalid_expiry_date": True,
    }
