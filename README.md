# Grocery Assistant MCP — Version 1.3

## Overview

Grocery Assistant MCP is a local Model Context Protocol server for working with grocery inventory, food intake, food waste, and inventory consumption records.

Version 1.3 builds on the Version 1.2 relationship-safe intake editing foundation by adding controlled inventory consumption workflows. Version 1.2 made it possible to search, update, and remove intake records without breaking the parent-child relationship between meal entries and item rows. Version 1.3 now adds explicit tools for reducing tracked inventory and recording why inventory changed.

The project currently uses local CSV files as the data layer. Core service functions read, write, validate, and protect these files, while MCP resources and tools expose selected behaviour to an MCP-compatible client.

The main principle for Version 1.3 is:

> Inventory should only be consumed through explicit, tested consumption workflows.

Version 1.3 intentionally avoids hidden side effects. Ordinary intake logging still does not automatically deduct inventory. Inventory is deducted only when the user calls a controlled consumption tool.

---

## Version 1.3 Capabilities

Version 1.3 supports all Version 1.2 capabilities plus:

- controlled inventory-only consumption
- intake-linked inventory consumption
- inventory consumption event logging
- a new inventory consumption resource
- canonical inventory stock statuses
- item-level `quantity_used` and `unit` tracking in intake item rows
- service-layer tests for inventory consumption workflows
- MCP tool registration for consumption tools
- resource registration for inventory consumption records

The major Version 1.3 workflow addition is:

```text
consume_inventory_item
    ↓
update inventory quantity / servings
    ↓
record user_inventory_consumption.csv event
```

And the linked intake workflow is:

```text
add_intake_entry
    ↓
add_intake_item_from_inventory
    ↓
create child intake item
    ↓
deduct inventory
    ↓
record linked inventory consumption event
```

---

## Version 1.3 Boundaries

Version 1.3 does **not** yet support:

- automatic inventory deduction from ordinary `add_intake_item`
- automatic batch meal parsing
- automatic recipe-level inventory deduction
- automatic reversal of inventory consumption when intake items are edited or removed
- automatic parent meal total recalculation after adding inventory-linked child items
- shopping list generation
- meal planning intelligence
- restock recommendation intelligence
- waste pattern analysis automation

These are planned for later versions.

The boundary is important because intake, inventory, and consumption are related but not identical. A meal may come from a restaurant, takeaway, shared food, leftovers, or untracked ingredients. For that reason, `stock_id` on a normal intake item can identify a relationship, but it should not silently mutate inventory.

Version 1.3 adds explicit tools for inventory mutation instead.

---

## Data Layer

The project separates grocery data into purpose-specific CSV files.

```text
user_inventory.csv
user_intake_history.csv
user_intake_items.csv
user_inventory_consumption.csv
user_food_waste.csv
```

This separation keeps the data model easier to reason about.

---

### Inventory

`user_inventory.csv` stores the current tracked grocery stock state.

Inventory can include:

- currently available items
- low-stock items
- very-low-stock items
- out-of-stock items kept as restock signals
- expired items still physically present
- items the user commonly buys
- items kept as shopping or planning reminders

Keeping some out-of-stock items is intentional. It helps the assistant understand common staples, restock patterns, frequently used items, and items that may not be urgent to replace.

#### Canonical Stock Status Values

Version 1.3 uses this stock status vocabulary:

```text
in_stock
low
very_low
out
expired
```

Removed values from earlier examples:

```text
ok
very low
empty
used
removed
```

These older values should not be used in Version 1.3 data.

---

### Intake History

`user_intake_history.csv` stores parent meal or eating-event records.

Examples:

- breakfast
- lunch
- dinner
- snack
- drink
- dessert
- takeaway meal
- leftover meal

Each row describes the overall eating event.

---

### Intake Items

`user_intake_items.csv` stores child food/component records within a meal.

Example:

```text
intake_007  Dinner  Spaghetti bolognese
    ├── beef mince
    ├── spaghetti
    ├── tomato sauce
    └── parmesan
```

The parent-child relationship is:

```text
user_intake_history.csv
    intake_id
        ↓
user_intake_items.csv
    intake_id
```

`stock_id` inside an intake item is optional. This allows the item to link to inventory when known, while still supporting restaurant meals, takeaway meals, shared food, and untracked food.

Version 1.3 adds two important intake item fields:

```text
quantity_used
unit
```

These fields preserve machine-readable quantity information alongside the human-readable `amount_eaten` field.

Example:

```text
amount_eaten = "500 ml"
quantity_used = 500
unit = "ml"
servings_used = 0
```

---

### Inventory Consumption

`user_inventory_consumption.csv` records inventory usage events.

This file answers questions such as:

- why did inventory quantity decrease?
- was the inventory reduction linked to an intake item?
- how much quantity or how many servings were used?
- what was the before/after stock state?
- was the consumption estimate low, medium, or high confidence?

Inventory consumption records can be created by:

```text
consume_inventory_item
add_intake_item_from_inventory
```

Inventory consumption is separate from food waste. Normal consumption is not waste.

---

### Food Waste

`user_food_waste.csv` records meaningful negative outcomes from food ownership.

Examples:

- expired
- spoiled
- discarded
- unused
- overbought
- did not like

Food waste records are created through `remove_inventory_item()` when the removal type is waste-related.

---

## Core Service Layer

Main file:

```text
grocery_assistant_mcp/core/grocery_service.py
```

The core service is responsible for:

- reading CSV files
- writing CSV files
- validating input
- generating IDs
- enforcing inventory, intake, consumption, and waste rules
- protecting parent-child intake relationships
- preventing over-consumption
- recording inventory consumption events
- converting data into JSON-ready dictionaries

The MCP tool layer should remain thin. Business rules should stay in the service layer.

---

## Generic Write Helpers

Main file:

```text
grocery_assistant_mcp/core/write_helpers.py
```

Generic helpers are used for reusable write behaviour such as:

- cleaning text
- validating dates
- validating times
- validating non-negative numbers
- validating integer ranges
- reading CSV files for writing
- backing up CSV files before writes
- saving CSV files
- generating the next ID
- requiring non-empty fields

Domain-specific rules should not live in this file. Rules such as valid stock statuses, valid meal types, consumption types, and waste-related removal types belong in the service layer.

---

## MCP Resources

### Inventory Resource

```text
grocery://inventory
```

Returns the current inventory records.

---

### Intake Resources

```text
grocery://intake/history
grocery://intake/items
grocery://intake-items
```

The `grocery://intake-items` resource is a legacy/compatibility alias for intake item records.

---

### Inventory Consumption Resource

```text
grocery://inventory-consumption
```

Returns inventory consumption event records.

This resource explains why inventory changed over time. It includes inventory-only consumption events and intake-linked consumption events.

---

### Food Waste Resources

```text
grocery://food-waste
grocery://food-waste/expired
```

These expose food waste records and expired-related waste records.

---

## MCP Tools

### Inventory Tools

```text
search_inventory
add_inventory_item
update_inventory_item
remove_inventory_item
```

#### `search_inventory`

Searches inventory by text, category, and/or location.

Typical uses:

- find chicken
- show pantry items
- show freezer proteins
- find use-soon items

#### `add_inventory_item`

Adds a new item to the inventory CSV.

Expected behaviour:

- validates required fields
- rejects negative quantity values
- rejects invalid dates
- generates a new `stock_id`
- stores initial quantity/serving values for later comparison
- validates Version 1.3 stock status values
- backs up the CSV before saving

Do not use this tool to reduce stock. Use `consume_inventory_item` or `add_intake_item_from_inventory` instead.

#### `update_inventory_item`

Updates an existing inventory item.

Expected behaviour:

- requires an existing `stock_id`
- updates only supplied fields
- validates dates and numeric fields
- validates stock status consistency
- preserves fields that are not provided

#### `remove_inventory_item`

Removes an inventory item from active tracking.

Expected behaviour:

- requires an existing `stock_id`
- validates the removal type
- removes the inventory row from active tracking
- creates a food waste record only for waste-related removal types

Waste-related removal types:

```text
expired
spoiled
discarded
unused
overbought
did_not_like
```

Non-waste removal types:

```text
used_up
duplicate_entry
incorrect_entry
test_entry
no_longer_tracked
unknown
```

---

### Intake Tools

```text
get_recent_intake
get_daily_intake_summary
search_intake
add_intake_entry
add_intake_item
update_intake_entry
update_intake_item
remove_intake_item
remove_intake_entry
```

#### `get_recent_intake`

Returns recent intake history for a selected number of days, optionally filtered by meal type.

#### `get_daily_intake_summary`

Returns a daily intake summary for a selected date.

The summary can use:

- item-level nutrition totals where available
- meal-level nutrition totals as fallback
- counts for missing nutrition values

#### `search_intake`

Searches both parent intake entries and child intake item records.

This is a read-only workflow tool. It helps locate `intake_id` and `intake_item_id` values before calling update or remove tools.

Supported filters include:

- `query`
- `intake_id`
- `intake_item_id`
- `date`
- `date_from`
- `date_to`
- `meal_type`
- `source`
- `stock_id`
- `category`
- `limit`

Expected behaviour:

- searches parent meal/eating-event records
- searches child ingredient/component records
- returns matching parent entries in `matching_entries`
- returns matching child items in `matching_items`
- includes `child_item_count` on parent entries
- includes `can_remove_entry` on parent entries
- includes parent meal context on child item results
- keeps search read-only and deterministic

Important search rule:

```text
Parent query results match parent fields.
Child query results match child fields.
Matched child results include parent context.
Matched parent results include child count, not automatically all children.
```

#### `add_intake_entry`

Creates a parent meal/eating-event row.

Expected behaviour:

- requires a date
- requires a meal name
- validates date format
- validates time format when supplied
- validates meal type
- validates confidence/status fields
- rejects negative nutrition estimates
- does not automatically create child intake items
- does not automatically deduct inventory

#### `add_intake_item`

Creates a child ingredient/component row linked to an intake entry.

Expected behaviour:

- requires an existing `intake_id`
- requires a food item name
- accepts optional `stock_id`
- validates `stock_id` only when supplied
- supports `quantity_used`, `unit`, and `servings_used`
- rejects orphan intake items
- rejects negative quantity, serving, or nutrition values
- does not automatically deduct inventory
- does not create an inventory consumption record

Use this for restaurant meals, takeaway food, shared food, untracked ingredients, or historical estimates that should not reduce inventory.

#### `update_intake_entry`

Updates an existing parent meal/eating-event row.

Expected behaviour:

- requires an existing `intake_id`
- updates only supplied fields
- preserves fields that are not provided
- validates date and time values
- validates meal type
- validates confidence/status fields
- rejects negative nutrition estimates
- does not automatically update child intake items
- does not automatically deduct inventory

#### `update_intake_item`

Updates an existing child ingredient/component row.

Expected behaviour:

- requires an existing `intake_item_id`
- updates only supplied fields
- preserves fields that are not provided
- validates parent `intake_id` if changed
- validates `stock_id` if supplied
- validates `quantity_used`, `unit`, and `servings_used`
- rejects unknown parent intake entries
- rejects unknown stock IDs when a non-blank stock ID is supplied
- rejects negative quantity, serving, or nutrition values
- does not automatically update the parent meal totals
- does not automatically deduct inventory

#### `remove_intake_item`

Removes one child intake item.

Expected behaviour:

- requires an existing `intake_item_id`
- removes the selected child item only
- does not remove the parent intake entry
- does not restore inventory
- backs up the CSV before saving

Use this before removing a parent intake entry that still has child items.

#### `remove_intake_entry`

Removes one parent intake entry only when it has no child intake items.

Expected behaviour:

- requires an existing `intake_id`
- checks whether child intake items exist
- blocks removal if child items are still attached
- tells the user to remove child items first
- removes the parent entry only after it is safe
- backs up the CSV before saving

Version 1.3 still does not cascade delete child intake items. This is intentional.

---

### Controlled Consumption Tools

```text
consume_inventory_item
add_intake_item_from_inventory
```

#### `consume_inventory_item`

Consumes part or all of a tracked inventory item without creating intake records.

Expected behaviour:

- requires an existing `stock_id`
- accepts `quantity_used` and/or `servings_used`
- requires at least one consumption amount greater than zero
- rejects negative consumption amounts
- rejects over-consumption
- updates `user_inventory.csv`
- creates a `user_inventory_consumption.csv` event
- does not create intake records
- does not remove the inventory row
- does not create a food waste record

Use this when the user says they used, drank, ate, cooked with, or finished a tracked inventory item but the event should not be attached to a meal.

#### `add_intake_item_from_inventory`

Creates a child intake item from inventory, reduces inventory, and records a linked consumption event.

Expected behaviour:

- requires an existing parent `intake_id`
- requires an existing inventory `stock_id`
- copies food item identity fields from inventory
- records `quantity_used`, `unit`, and `servings_used` on the child intake item
- updates `user_inventory.csv`
- appends a linked `user_inventory_consumption.csv` record
- links the consumption record to the created `intake_item_id`
- does not create the parent meal entry
- does not modify parent meal-level nutrition totals
- does not remove the inventory row
- does not create a food waste record

Use this when the user ate or used a known inventory item as part of an existing meal or eating event.

---

## Recommended ID Style

Use one consistent ID style across the project.

Recommended:

```text
inv_001
intake_001
intake_item_001
consumption_001
waste_001
```

Avoid mixing styles such as:

```text
INTAKE-0005
intake_005
inv_001
```

Consistent IDs make examples, tests, debugging, and documentation easier.

---

## Running the Server

Run commands from the project root:

```powershell
cd C:\Users\shann\TafeLocal\rest-at2\grocery-assistant-mcp
```

### Run the stdio server

```powershell
python -m grocery_assistant_mcp.stdio_server
```

### Run the streamable HTTP server

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

A browser request to `/` may return `404 Not Found`.

A browser request to `/mcp` may return `406 Not Acceptable`.

This is expected because the MCP endpoint expects MCP JSON-RPC requests, not normal browser page requests.

---

## Testing

Run the test suite from the project root:

```powershell
pytest -q
```

Useful focused tests:

```powershell
pytest tests/test_inventory_consumption.py -q
pytest tests/test_intake_edit_delete_service.py -q
pytest tests/test_search_intake_service.py -q
pytest tests/test_mcp_tool_registration.py -q
pytest tests/test_mcp_resource_registration.py -q
```

Version 1.3 was validated with:

- service-layer tests for controlled inventory consumption
- service-layer tests for linked intake/inventory consumption
- tests for the inventory consumption event log
- data-file schema tests
- resource payload tests
- MCP tool registration checks
- MCP resource registration checks
- MCP Inspector manual testing
- curl/manual HTTP testing, where applicable

---

## Documentation Map

Recommended documentation files for Version 1.3:

```text
README.md
docs/project_roadmap.md
docs/version_1_3_completion_checklist.md
docs/mcp_testing_guide_v1_3.md
docs/command_reference.md
docs/development_journal_v1_3.md
docs/future_version_plans.md
```

---

## Final Version 1.3 Definition

Version 1.3 is complete when:

- `consume_inventory_item` reduces inventory safely
- `consume_inventory_item` records an inventory consumption event
- `add_intake_item_from_inventory` creates an intake item and reduces inventory
- linked consumption events include `intake_id` and `intake_item_id`
- intake items store `quantity_used`, `unit`, and `servings_used`
- inventory uses canonical stock statuses
- ordinary `add_intake_item` does not deduct inventory
- ordinary `add_intake_item` does not create consumption records
- consumption does not create food waste records
- over-consumption is rejected
- invalid stock IDs are rejected
- invalid parent intake IDs are rejected
- service-layer tests pass
- MCP tool registration tests pass
- MCP resource registration tests pass
- MCP Inspector can call the Version 1.3 tools
- documentation clearly explains the Version 1.3 scope boundary
