# Version 1.2 Completion Checklist

## Version Name

Version 1.2 — Intake Relationship Editing and Cleanup

## Status

```text
Service-layer tests: PASSED
Search intake tests: PASSED
MCP Inspector testing: PASSED
Curl manual testing: DEFERRED
Documentation: UPDATED
Final commit: PENDING
```

## Goal

Version 1.2 adds relationship-safe intake search, editing, and cleanup tools.

The main goal is to support this workflow:

```text
Find intake record
    ↓
Inspect parent-child relationship
    ↓
Update parent or child record
    ↓
Remove child item if needed
    ↓
Remove parent entry only when safe
```

## Core Principle

> Find and inspect intake records before editing or removing them.

Version 1.2 keeps cleanup conservative. Parent intake entries cannot be removed while child intake items still exist.

---

## Implemented Service Functions

```text
[x] search_intake
[x] update_intake_entry
[x] update_intake_item
[x] remove_intake_item
[x] remove_intake_entry
[x] relationship helper checks
[x] parent-child removal protection
[x] numeric dtype handling for decimal updates
```

---

## Implemented MCP Tools

```text
[x] search_intake
[x] update_intake_entry
[x] update_intake_item
[x] remove_intake_item
[x] remove_intake_entry
```

---

## `search_intake` Behaviour

```text
[x] searches parent intake entries
[x] searches child intake item records
[x] supports text query search
[x] supports direct intake_id lookup
[x] supports direct intake_item_id lookup
[x] supports exact date filtering
[x] supports date range filtering
[x] supports meal type filtering
[x] supports source filtering
[x] supports stock ID filtering
[x] supports category filtering
[x] applies a safe result limit
[x] caps very large limits
[x] returns matching_entries
[x] returns matching_items
[x] includes parent context on child item results
[x] includes child item count on parent results
[x] includes can_remove_entry on parent results
```

Search design rule:

```text
Parent query results match parent fields.
Child query results match child fields.
Matched child results include parent context.
Matched parent results include child count, not automatically all children.
```

---

## Intake Update Behaviour

```text
[x] update_intake_entry requires an existing intake_id
[x] update_intake_entry updates only supplied fields
[x] update_intake_entry preserves unchanged fields
[x] update_intake_entry validates date and time values
[x] update_intake_entry validates meal type
[x] update_intake_entry validates confidence/status fields
[x] update_intake_entry rejects negative nutrition values

[x] update_intake_item requires an existing intake_item_id
[x] update_intake_item updates only supplied fields
[x] update_intake_item preserves unchanged fields
[x] update_intake_item validates parent intake_id if changed
[x] update_intake_item validates stock_id if supplied
[x] update_intake_item rejects negative serving/nutrition values
```

---

## Intake Removal Behaviour

```text
[x] remove_intake_item removes one child item
[x] remove_intake_item does not remove the parent entry
[x] remove_intake_entry removes a parent only when no child items exist
[x] remove_intake_entry blocks removal when child items exist
[x] no cascade deletion occurs in Version 1.2
[x] orphan child intake items are avoided
```

---

## Tests

```text
[x] tests/test_intake_edit_delete_service.py passes
[x] tests/test_search_intake_service.py passes
[x] tests/test_mcp_tool_registration.py passes
[x] full pytest suite passes
```

Useful commands:

```powershell
pytest tests/test_intake_edit_delete_service.py -q
pytest tests/test_search_intake_service.py -q
pytest tests/test_mcp_tool_registration.py -q
pytest -q
```

---

## Manual Testing

```text
[x] MCP Inspector lists the Version 1.2 tools
[x] MCP Inspector can call search_intake
[x] MCP Inspector can call update_intake_entry
[x] MCP Inspector can call update_intake_item
[x] MCP Inspector can call remove_intake_item
[x] MCP Inspector confirms remove_intake_entry blocks unsafe parent deletion
[x] MCP Inspector confirms remove_intake_entry succeeds after child items are removed
```

---

## Deferred Testing Note

Curl-based Streamable HTTP testing was not completed during the main Version 1.2 implementation pass.

Version 1.2 functionality was validated through:

- service-layer pytest tests
- MCP tool registration tests
- MCP Inspector manual testing

Curl request examples should be added later as documentation/supporting verification for the Streamable HTTP workflow.

---

## Explicitly Out of Scope

Version 1.2 does not add:

- automatic inventory deduction
- inventory consumption tools
- automatic meal parsing
- automatic parent-child batch meal creation
- automatic child item cascade deletion
- shopping list generation
- meal planning intelligence
- restock recommendation intelligence
- waste pattern analysis

---

## Final Completion Statement

Version 1.2 is complete when relationship-safe intake search, editing, and cleanup are implemented, tested, exposed through MCP tools, and documented.

The version should close with the project still following the same architecture principle:

```text
CSV files
    ↓
core service functions
    ↓
thin MCP resources/tools
    ↓
MCP-compatible client
```
