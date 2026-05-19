# Version 1.5D Development Files

This package contains the proposed Version 1.5D restock suggestion implementation.

## Purpose

Version 1.5D adds a read-only restock reasoning tool:

```text
draft_restock_suggestions
```

It ranks possible restocks from:

- low and very-low inventory signals
- out-of-stock inventory signals
- expired replacement signals
- meal-gap signals from `draft_meal_suggestions`
- cautious generic role gaps, such as `vegetable option`, when no exact tracked item exists

It does **not** create shopping-list rows, update inventory, deduct stock, log intake, or create waste records.

## Files

```text
core/restock_helpers.py
  New Version 1.5D helper module.

core/grocery_service.py
  Updated to import `build_restock_suggestion_draft` and expose `draft_restock_suggestions`.

core/meal_suggestion_helpers.py
  Updated with backward-compatible structured fields on meal match and gap signals.

mcp_tools/planning_tools.py
  Updated to expose the MCP tool wrapper `draft_restock_suggestions_tool`.

tests/test_draft_restock_suggestions.py
  New test coverage for the restock draft behaviour.

docs/version_1_5d_restock_suggestion_architecture.md
  Architecture and investigation documentation.
```

## Integration notes

Copy files into their matching project folders:

```text
grocery_assistant_mcp/core/restock_helpers.py
grocery_assistant_mcp/core/grocery_service.py
grocery_assistant_mcp/core/meal_suggestion_helpers.py
grocery_assistant_mcp/mcp_tools/planning_tools.py
tests/test_draft_restock_suggestions.py
docs/version_1_5d_restock_suggestion_architecture.md
```

Then run:

```powershell
pytest -q
```

If your server registration imports `register_planning_tools`, the restock tool should appear through the updated `planning_tools.py`. If your project uses a separate registry pattern, import and register the updated planning tools as normal.
