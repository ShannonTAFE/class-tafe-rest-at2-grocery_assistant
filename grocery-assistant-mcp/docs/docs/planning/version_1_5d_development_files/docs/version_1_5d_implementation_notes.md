# Version 1.5D — Implementation Notes

## Implemented capability

```text
draft_restock_suggestions
```

This is a read-only restock reasoning tool. It prepares draft restock suggestions from inventory and meal-gap signals without creating shopping-list rows or mutating any grocery records.

## Main files changed or added

```text
Added:
  grocery_assistant_mcp/core/restock_helpers.py
  tests/test_draft_restock_suggestions.py

Updated:
  grocery_assistant_mcp/core/grocery_service.py
  grocery_assistant_mcp/core/meal_suggestion_helpers.py
  grocery_assistant_mcp/mcp_tools/planning_tools.py
```

## Behaviour

The new service function reads inventory and prepares restock suggestions from:

```text
low / very-low stock
out-of-stock records
expired replacement needs
meal-gap hints from draft_meal_suggestions
generic role gaps such as vegetable option, when no exact tracked item exists
```

The response includes:

```text
tool_name
summary
result_type = restock_suggestion_draft
status
inputs
signals
suggestions
warnings
next_actions
safety
metadata
```

## Safety boundary

Version 1.5D does not:

```text
create shopping-list records
update inventory
deduct inventory
log intake
create waste records
```

All returned suggestions include:

```text
would_create_shopping_list_record: false
requires_user_confirmation_before_write: true
```

The response-level safety metadata also preserves the existing read-only planning contract.

## Meal suggestion helper refinement

`meal_suggestion_helpers.py` was updated to add structured context to meal match and gap signals:

```text
template_id
template_name
matched_roles
supporting_roles
optional_roles
gap_role
requiredness
meal_name on gap signals
```

This lets restock suggestions use structured meal evidence instead of parsing human-readable `restock_hint` text.

## Testing

New tests cover:

```text
empty inventory
low-stock restock drafts
out-of-stock restock drafts
expired replacement drafts
meal-gap priority elevation
optional upgrade disabling
max_suggestions limit
read-only safety contract
```

Recommended project check:

```powershell
pytest -q
```

A syntax compile check was completed on the generated Python files in this environment. Full pytest should be run inside your project repository because this isolated environment does not include the full package tree and CSV fixtures.
