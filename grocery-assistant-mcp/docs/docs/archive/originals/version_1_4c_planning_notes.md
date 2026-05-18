# Version 1.4C Planning Notes — Batch Inventory-Linked Meal Logging

## Purpose

This document prepares the project to begin Version 1.4C after Version 1.4B batch meal logging.

Version 1.4B created a safe intake-only batch workflow:

```text
add_meal_with_items
```

Version 1.4C should add an explicit inventory-linked batch workflow.

Candidate tool:

```text
add_meal_with_inventory_items
```

---

## Core Difference From Version 1.4B

Version 1.4B:

```text
Creates parent intake entry
Creates child intake item rows
Does not deduct inventory
Does not create consumption records
```

Version 1.4C:

```text
Creates parent intake entry
Creates child intake item rows
Deducts selected inventory items
Creates linked inventory consumption records
```

This must be a separate explicit workflow.

Do not add inventory deduction to `add_meal_with_items`.

---

## Core Principle

> Inventory-linked batch meal logging must validate the entire batch before writing anything.

This protects against partial states such as:

```text
parent meal created but child items failed
child items created but inventory deduction failed
inventory deducted but consumption event failed
consumption event created without matching intake item
```

---

## Candidate Request Shape

A possible request shape:

```json
{
  "meal_data": {
    "date": "2026-05-18",
    "time": "18:30",
    "meal_type": "dinner",
    "meal_name": "Spaghetti bolognese",
    "source": "home",
    "amount_eaten": "1 bowl"
  },
  "items": [
    {
      "stock_id": "inv_001",
      "amount_eaten": "1 serve",
      "quantity_used": 100,
      "unit": "g",
      "servings_used": 1,
      "nutrition_confidence": "medium",
      "notes": "Spaghetti from pantry"
    },
    {
      "stock_id": "inv_002",
      "amount_eaten": "1 serve",
      "quantity_used": 125,
      "unit": "g",
      "servings_used": 1,
      "nutrition_confidence": "medium",
      "notes": "Beef mince from freezer"
    }
  ],
  "consumption_type": "meal",
  "tracking_confidence": "medium",
  "notes": "Inventory-linked batch meal logging test"
}
```

Open design question:

```text
Should consumption_type and tracking_confidence live at the batch level, item level, or both?
```

Recommendation:

```text
Start with item-level values if different items may have different confidence.
Allow batch-level defaults only if implementation stays clear.
```

---

## Candidate Return Shape

```json
{
  "success": true,
  "message": "Inventory-linked meal and child intake items added.",
  "intake_entry": {},
  "intake_items": [],
  "consumption_records": [],
  "inventory_updates": [],
  "item_count": 0,
  "inventory_deducted": true,
  "consumption_records_created": 0,
  "food_waste_records_created": 0,
  "backup_paths": {}
}
```

---

## Validation Rules to Decide Before Implementation

### Parent Meal Validation

```text
Use the same parent meal validation as Version 1.4B.
Reject unsupported meal_data fields.
Do not generate intake_id until all validation can pass.
```

### Inventory Item Validation

Each inventory-linked item should:

```text
require an existing stock_id
require quantity_used > 0 and/or servings_used > 0
reject negative quantity_used
reject negative servings_used
reject use greater than available inventory
copy food_item, brand, category, and unit from inventory where appropriate
```

### Duplicate stock_id Handling

This is the most important new Version 1.4C issue.

If the same stock_id appears more than once in the batch, validation must aggregate the total intended use before checking availability.

Example:

```text
Item 1 uses 60g of inv_001
Item 2 uses 60g of inv_001
Inventory only has 100g
```

Each item individually looks valid, but the batch total is invalid.

Version 1.4C must reject this before any write.

### Unit Handling

Open design question:

```text
Should the tool require the item unit to match the inventory unit?
```

Recommended first rule:

```text
If quantity_used is supplied, use the inventory row's unit in the generated intake item.
Do not attempt unit conversion in Version 1.4C.
Reject ambiguous conversions.
```

### Partial Write Prevention

The workflow should build all updated DataFrames in memory first:

```text
updated_intake_history_df
updated_intake_items_df
updated_inventory_df
updated_inventory_consumption_df
```

Only after all validation and row-building succeeds should the workflow call `save_related_csv_updates`.

---

## Files Likely Needed

Possible new or updated files:

```text
grocery_assistant_mcp/core/batch_inventory_meal_service.py
grocery_assistant_mcp/core/grocery_service.py
grocery_assistant_mcp/mcp_tools/batch_meal_tools.py
tests/test_batch_inventory_meal_service.py
tests/test_mcp_tool_registration.py
```

Alternative:

```text
Extend batch_meal_service.py if the file remains manageable.
```

Recommendation:

```text
Use a separate batch_inventory_meal_service.py if the validation logic becomes large.
```

---

## Tests to Write First

```text
test_add_meal_with_inventory_items_creates_parent_children_inventory_updates_and_consumption_records
test_add_meal_with_inventory_items_rejects_missing_stock_id_without_writing
test_add_meal_with_inventory_items_rejects_unknown_stock_id_without_writing
test_add_meal_with_inventory_items_rejects_overuse_without_writing
test_add_meal_with_inventory_items_rejects_duplicate_stock_id_aggregate_overuse_without_writing
test_add_meal_with_inventory_items_links_consumption_records_to_child_items
test_add_meal_with_inventory_items_records_inventory_before_after_state
test_add_meal_with_inventory_items_does_not_create_food_waste_records
test_add_meal_with_inventory_items_rolls_back_all_related_csvs_on_save_failure
```

The most important test is:

```text
If any one child inventory deduction is invalid, no parent meal, child item, inventory update, or consumption record should be written.
```

---

## MCP Tool Description Boundary

The MCP tool description should be explicit:

```text
Use this tool only when the user clearly wants a meal logged from tracked inventory and inventory should be deducted.

This tool creates a parent intake entry, child intake items, inventory deductions, and linked consumption records.

Do not use this tool for ordinary meal logging where the user only says what they ate.
Use add_meal_with_items for intake-only batch meal logging.
```

---

## Example Intent Split

Use `add_meal_with_items` when the user says:

```text
I ate spaghetti bolognese with pasta, mince, sauce, and parmesan.
```

Use `add_meal_with_inventory_items` only when the user says something like:

```text
I made spaghetti bolognese using 100g pasta from inventory and 125g beef mince from the freezer. Log it and update my stock.
```

If the user says:

```text
I ate spag bog.
```

Do not deduct inventory.

That request may use aliases/templates in a future learning version, but inventory mutation should remain explicit.
