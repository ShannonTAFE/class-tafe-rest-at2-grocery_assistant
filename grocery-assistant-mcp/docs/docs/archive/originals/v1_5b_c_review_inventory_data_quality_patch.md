# Version 1.5B-C Patch — `review_inventory_data_quality`

This patch adds the third focused Version 1.5B inventory planning review tool.

## Goal

```text
review_inventory_data_quality
```

## Purpose

Return a read-only focused review of inventory data-quality signals.

This completes the first Version 1.5B focused-review trio:

```text
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
```

## Scope

This tool is still a review tool, not a recommendation or write tool.

It should:

```text
reuse build_planning_context()
filter existing data-quality signals
return a standard planning response
keep recommendations empty
preserve read-only safety metadata
route write actions through confirmation-only next actions
```

It should not:

```text
update inventory
infer corrections automatically
create shopping list records
deduct inventory
save recommendation feedback
```

## Files

Place these files into your repo:

```text
grocery_assistant_mcp/core/planning_service.py
grocery_assistant_mcp/mcp_tools/planning_tools.py
tests/test_planning_inventory_data_quality_review.py
grocery_assistant_mcp/docs/curl_requests/18_review_inventory_data_quality.json
```

## Test commands

```powershell
pytest tests/test_planning_inventory_data_quality_review.py -v
pytest
```

## MCP Inspector check

Confirm the tool appears:

```text
review_inventory_data_quality
```

Expected response:

```text
tool_name: review_inventory_data_quality
result_type: inventory_data_quality_review
recommendations: []
safety.read_only: true
signals.data_quality_signals contains selected data-quality signals only
```
