# Version 1.4B Completion Checklist

## Version Name

Version 1.4B — Batch Meal Logging

## Status

```text
Service-layer batch meal tests: PASSED
Full pytest suite: PASSED
MCP tool registration: PASSED
MCP Inspector manual test: PASSED / READY TO RECORD
Documentation: UPDATED FOR 1.4B CLOSEOUT
Next stage: READY FOR VERSION 1.4C PLANNING
```

---

## Goal

Version 1.4B adds a safe batch intake workflow for logging one meal with multiple child intake items.

The core workflow is:

```text
User describes one meal
    ↓
System creates one parent intake entry
    ↓
System creates multiple child intake item rows
    ↓
All child rows link to the created parent intake_id
```

The main service/tool is:

```text
add_meal_with_items
```

---

## Core Principle

> Batch meal logging is an intake workflow, not an inventory mutation workflow.

Version 1.4B may recognise and record meal components, but it does not deduct stock.

This preserves the project rule introduced in Version 1.3:

```text
Inventory should only be reduced through explicit, tested consumption tools.
```

---

## Implemented Behaviour

```text
[x] Creates one parent intake entry
[x] Creates one or more child intake item rows
[x] Links every child item to the created parent intake_id
[x] Generates a new intake_id
[x] Generates sequential intake_item_id values
[x] Validates parent meal data before writing
[x] Validates every child item before writing
[x] Rejects an empty child item list
[x] Rejects unsupported parent fields
[x] Rejects unsupported child item fields
[x] Validates stock_id if supplied on a child item
[x] Treats stock_id as a reference only
[x] Saves intake history and intake items together
[x] Returns created parent entry and child items
[x] Returns item_count
[x] Returns inventory_deducted=false
[x] Returns consumption_records_created=0
[x] Returns food_waste_records_created=0
```

---

## Explicit Non-Goals

Version 1.4B intentionally does not:

```text
[x] deduct inventory
[x] create inventory consumption records
[x] create food waste records
[x] auto-calculate parent meal nutrition from child items
[x] create meal aliases
[x] create meal templates
[x] learn user meal patterns automatically
[x] handle recipe-level consumption
[x] handle batch cooking or leftovers as stock objects
```

These boundaries keep Version 1.4B safe and prepare the project for Version 1.4C.

---

## Files Added or Updated

Expected implementation files:

```text
grocery_assistant_mcp/core/batch_meal_service.py
grocery_assistant_mcp/core/grocery_service.py
grocery_assistant_mcp/mcp_tools/batch_meal_tools.py
grocery_assistant_mcp/mcp_tools/register.py
tests/test_batch_meal_service.py
tests/test_mcp_tool_registration.py
```

Possible testing cleanup files:

```text
pytest.ini
.gitignore
```

---

## Service Function

```text
add_meal_with_items(meal_data, items)
```

### Writes To

```text
user_intake_history.csv
user_intake_items.csv
```

### Does Not Write To

```text
user_inventory.csv
user_inventory_consumption.csv
user_food_waste.csv
```

---

## Expected Return Shape

The response should include:

```json
{
  "success": true,
  "message": "Meal and child intake items added.",
  "intake_entry": {},
  "intake_items": [],
  "item_count": 0,
  "inventory_deducted": false,
  "consumption_records_created": 0,
  "food_waste_records_created": 0,
  "intake_history_backup_created": "...",
  "intake_items_backup_created": "..."
}
```

The exact backup path values may vary depending on the local environment.

---

## Example Use Case

User request:

```text
I had spaghetti bolognese for dinner with spaghetti, beef mince, tomato sauce, and parmesan.
```

Expected Version 1.4B behaviour:

```text
Create parent intake entry:
    Dinner — Spaghetti bolognese

Create child intake items:
    spaghetti
    beef mince
    tomato sauce
    parmesan

Do not deduct inventory.
Do not create inventory consumption events.
Do not create food waste records.
```

---

## Tests

Recommended test commands:

```powershell
pytest tests/test_batch_meal_service.py -q
pytest tests/test_mcp_tool_registration.py -q
pytest -q
```

The Version 1.4B test suite should confirm:

```text
[x] parent and child rows are created
[x] child rows link to the created parent intake_id
[x] invalid child rows prevent all writes
[x] invalid parent data prevents all writes
[x] supplied stock_id values are validated
[x] blank stock_id values are allowed
[x] inventory is not updated
[x] consumption records are not created
[x] food waste records are not created
[x] MCP tool is registered
```

---

## MCP Inspector Manual Test

Start the streamable HTTP server:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Open MCP Inspector in another terminal:

```powershell
npx @modelcontextprotocol/inspector
```

Connect using:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
```

Select tool:

```text
add_meal_with_items
```

Paste only the tool arguments, not the full JSON-RPC wrapper:

```json
{
  "meal_data": {
    "date": "2026-05-18",
    "time": "18:30",
    "meal_type": "dinner",
    "meal_name": "Spaghetti bolognese",
    "source": "home",
    "amount_eaten": "1 bowl",
    "portion_confidence": "medium",
    "nutrition_confidence": "medium",
    "was_finished": "yes",
    "leftovers_created": "no",
    "notes": "MCP Inspector batch meal logging test"
  },
  "items": [
    {
      "food_item": "Spaghetti",
      "category": "pantry",
      "source": "home",
      "amount_eaten": "1 serve",
      "quantity_used": 100,
      "unit": "g",
      "servings_used": 1,
      "nutrition_confidence": "medium",
      "notes": "Child item test"
    },
    {
      "food_item": "Beef mince",
      "category": "protein",
      "source": "home",
      "amount_eaten": "1 serve",
      "quantity_used": 125,
      "unit": "g",
      "servings_used": 1,
      "nutrition_confidence": "medium",
      "notes": "Child item test"
    }
  ]
}
```

Expected result:

```text
success = true
item_count = 2
inventory_deducted = false
consumption_records_created = 0
food_waste_records_created = 0
```

Expected CSV result:

```text
user_intake_history.csv gains one parent row
user_intake_items.csv gains two child rows
user_inventory.csv is unchanged
user_inventory_consumption.csv is unchanged
user_food_waste.csv is unchanged
```

---

## Version 1.4B Completion Definition

Version 1.4B is complete when:

```text
[x] add_meal_with_items service is implemented
[x] service-layer tests pass
[x] full pytest suite passes
[x] MCP tool is registered
[x] MCP Inspector can call the tool successfully
[x] CSV results match the intake-only boundary
[x] documentation records the Version 1.4B boundary
[x] Version 1.4C scope is clearly separated
```

---

# Version 1.4C Handoff

Version 1.4C should build on Version 1.4B by adding an explicit inventory-linked batch meal workflow.

Candidate tool:

```text
add_meal_with_inventory_items
```

Goal:

```text
Create one parent intake entry
Create multiple child intake item rows
Deduct selected inventory items
Create linked inventory consumption records
Save all related CSV updates safely
```

Version 1.4C may write to:

```text
user_intake_history.csv
user_intake_items.csv
user_inventory.csv
user_inventory_consumption.csv
```

It should still avoid food waste records unless the workflow explicitly includes waste handling.

Important Version 1.4C rules:

```text
All input must validate before any write.
Inventory deduction must be explicit.
Duplicate stock_id usage must be aggregated before validation.
No parent meal should be created if inventory deduction validation fails.
No child item should be created unless all linked inventory deductions can succeed.
No consumption record should be created unless the matching child intake item is created.
Each consumption event must link to both intake_id and intake_item_id.
Inventory before/after state must be recorded for every deduction.
```

Recommended first Version 1.4C task:

```text
Plan the request shape for add_meal_with_inventory_items before writing code.
```

Do not begin with implementation until the request structure, validation rules, duplicate stock handling, and rollback expectations are clear.
