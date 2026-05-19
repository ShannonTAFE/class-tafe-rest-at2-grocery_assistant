# Version 1.5B-B Patch — `review_use_soon_items`

This patch adds the second focused Version 1.5B planning review tool.

## Goal

```text
review_use_soon_items
```

## Purpose

Return a read-only focused review of expiry-related inventory signals:

```text
use_soon
expired
no_expiry_data
invalid_expiry_date
```

This tool reuses the Version 1.5A/1.5B planning signal layer and does not create meal recommendations, shopping-list items, inventory mutations, or waste records.

---

## Files included

```text
grocery_assistant_mcp/core/planning_service.py
grocery_assistant_mcp/mcp_tools/planning_tools.py
tests/test_planning_use_soon_review.py
grocery_assistant_mcp/docs/curl_requests/17_review_use_soon_items.json
```

The included Python files are full replacement files based on the Version 1.5B-A low-stock implementation.

---

## Service behaviour

`review_use_soon_items()`:

1. Calls `build_planning_context()` with inventory enabled and recent intake disabled.
2. Filters inventory signals to selected expiry-related types:
   - `use_soon`
   - `expired`
3. Filters data-quality signals to selected expiry-data types:
   - `no_expiry_data`
   - `invalid_expiry_date`
4. Returns a standard planning response with:
   - `tool_name = "review_use_soon_items"`
   - `result_type = "inventory_use_soon_review"`
   - `recommendations = []`
   - read-only safety metadata
   - `records_checked` metadata
   - confirmation-required write next actions

---

## MCP wrapper behaviour

The new MCP tool accepts these flags:

```python
include_use_soon: bool = True
include_expired: bool = True
include_no_expiry_data: bool = True
include_invalid_expiry_date: bool = True
```

It delegates directly to the service layer and does not contain business logic.

---

## Routing update

`build_planning_context()` now includes this read-only next action:

```json
{
  "action_type": "review_use_soon",
  "tool_name": "review_use_soon_items",
  "requires_confirmation": false
}
```

This mirrors the previous Version 1.5B-A low-stock routing pattern.

---

## Tests

Run the focused test:

```powershell
pytest tests/test_planning_use_soon_review.py -v
```

Then run the full suite:

```powershell
pytest
```

The test file protects:

```text
response contract
signal filtering
include flags
empty recommendations
read-only safety metadata
write next actions requiring confirmation
warning when no expiry signals are found
warning when no filters are selected
review_planning_context routing to review_use_soon_items
```

---

## MCP Inspector check

Start the server:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Confirm this tool appears:

```text
review_use_soon_items
```

Call it with default arguments.

Expected behaviour:

```text
returns only use_soon / expired inventory signals
returns only no_expiry_data / invalid_expiry_date data-quality signals
recommendations remains empty
safety.read_only is true
no records are changed
```
