# Grocery Assistant MCP — Version 1.1

## Overview

Grocery Assistant MCP is a local Model Context Protocol server for working with grocery inventory, food intake, and food waste records.

Version 1.1 finalises the first safe write layer of the project. Earlier Version 1 work focused mainly on read-only resources, search tools, summaries, prompts, and MCP testing. Version 1.1 adds controlled write tools for inventory and intake while keeping behaviour explicit, testable, and safe.

The project currently uses local CSV files as the data layer. Core service functions read and write these files, while MCP resources and tools expose selected behaviour to an MCP-compatible client.

The main principle for Version 1.1 is:

> Build a safe write foundation before adding automation.

Version 1.1 intentionally avoids hidden side effects such as automatically reducing inventory when logging meals. More intelligent workflows are planned for future versions after the data model and validation rules are stable.

---

## Version 1.1 Capabilities

Version 1.1 supports:

- reading current grocery inventory
- reading meal-level intake history
- reading ingredient/component-level intake records
- reading food waste records
- searching inventory
- adding inventory items
- updating inventory items
- removing inventory items
- creating food waste records through inventory removal
- adding parent intake entries
- adding child intake item records
- reviewing recent intake
- summarising daily intake

---

## Version 1.1 Boundaries

Version 1.1 does **not** yet support:

- automatic inventory deduction when logging intake
- automatic meal parsing from free text into ingredient rows
- automatic food waste inference from leftovers
- automatic shopping list generation
- batch meal logging across multiple CSV files
- editing or deleting intake parent/child relationships
- inventory consumption tools
- long-term waste pattern analysis

These are planned for later versions.

The boundary is important because intake, inventory, and waste are related but not identical. Eating a meal does not always mean a tracked inventory item should be reduced. A meal may come from a restaurant, takeaway, leftovers, shared food, or untracked ingredients.

---

## Data Layer

The project separates grocery data into purpose-specific CSV files.

```text
user_inventory.csv
user_food_waste.csv
user_intake_history.csv
user_intake_items.csv
```

This separation keeps the data model easier to reason about.

---

### Inventory

Inventory records food items that are useful for current or future grocery decisions.

Inventory can include:

- currently available items
- low-stock items
- empty or out-of-stock staples
- expired items still physically present
- items the user commonly buys
- items kept as shopping or planning reminders

Keeping some out-of-stock items is intentional. It helps the assistant understand common staples, restock patterns, and items that may not be urgent to replace.

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

`stock_id` inside an intake item is optional. This allows the item to link to inventory when known, while still supporting restaurant meals, takeaway meals, and untracked food.

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

In Version 1.1, food waste records are created through `remove_inventory_item()` when the removal type is waste-related.

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
- enforcing inventory, intake, and waste rules
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

Domain-specific rules should not live in this file. Rules such as valid stock statuses, valid meal types, and waste-related removal types belong in the service layer.

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
- backs up the CSV before saving

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
- removes or marks the inventory row according to the project behaviour
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
add_intake_entry
add_intake_item
```

#### `get_recent_intake`

Returns recent intake history for a selected number of days, optionally filtered by meal type.

#### `get_daily_intake_summary`

Returns a daily intake summary for a selected date.

The summary can use:

- item-level nutrition totals where available
- meal-level nutrition totals as fallback
- counts for missing nutrition values

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

#### `add_intake_item`

Creates a child ingredient/component row linked to an intake entry.

Expected behaviour:

- requires an existing `intake_id`
- requires a food item name
- accepts optional `stock_id`
- validates `stock_id` only when supplied
- rejects orphan intake items
- rejects negative serving or nutrition values

---

## Recommended ID Style

Use one consistent ID style across the project.

Recommended:

```text
inv_001
intake_001
intake_item_001
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
pytest tests/test_v1_1_write_foundation.py -q
pytest tests/test_mcp_tool_registration.py -q
```

Manual testing should also be done with MCP Inspector and curl.

See:

```text
docs/mcp_testing_guide.md
docs/command_reference.md
docs/version_1_1_completion_checklist.md
```

---

## Documentation Map

Recommended documentation files for Version 1.1:

```text
README.md
docs/project_roadmap.md
docs/version_1_1_completion_checklist.md
docs/mcp_testing_guide.md
docs/command_reference.md
docs/development_journal_v1_1.md
docs/future_version_plans.md
```

---

## Final Version 1.1 Definition

Version 1.1 is complete when:

- service-layer write functions are tested
- MCP tools are registered
- MCP Inspector can call the Version 1.1 tools
- invalid input is rejected clearly
- inventory removal can create waste safely
- intake items cannot be orphaned
- intake does not automatically deduct inventory
- documentation clearly explains the scope boundary
- future automation is deferred to later versions
