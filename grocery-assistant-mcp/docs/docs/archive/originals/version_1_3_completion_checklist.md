# Version 1.3 Completion Checklist

## Version Name

Version 1.3 — Controlled Inventory Consumption

## Status

```text
Service-layer tests: PASSED
Inventory consumption tests: PASSED
MCP tool registration tests: PASSED
MCP resource registration tests: PASSED
Data/resource payload tests: PASSED
MCP Inspector testing: IN PROGRESS / MANUAL
Curl manual testing: IN PROGRESS / MANUAL
Documentation: UPDATED
Automated baseline: 196 passed
Final commit: PENDING
```

## Goal

Version 1.3 adds explicit inventory consumption workflows.

The main goal is to support this workflow:

```text
Find inventory item
    ↓
Consume quantity and/or servings
    ↓
Update inventory state
    ↓
Record inventory consumption event
```

And this linked workflow:

```text
Find or create parent intake entry
    ↓
Add intake item from inventory
    ↓
Deduct inventory
    ↓
Record linked inventory consumption event
```

## Core Principle

> Inventory should only be reduced through explicit, tested consumption tools.

Ordinary intake logging does not automatically reduce inventory.

---

## Implemented CSV/Data Schema Changes

```text
[x] Added user_inventory_consumption.csv
[x] Added quantity_used to user_intake_items.csv
[x] Added unit to user_intake_items.csv
[x] Updated inventory stock_status values
[x] Removed old stock statuses from active schema
[x] Updated seed/demo CSV files
[x] Updated data-file validation tests
```

Version 1.3 stock status values:

```text
in_stock
low
very_low
out
expired
```

---

## Implemented Service Functions and Helpers

```text
[x] validate_consumption_amounts
[x] calculate_inventory_after_consumption
[x] apply_inventory_consumption_to_df
[x] build_inventory_consumption_record
[x] save_related_csv_updates
[x] consume_inventory_item
[x] add_intake_item_from_inventory
[x] read_inventory_consumption
[x] list_inventory_consumption
```

---

## Implemented MCP Tools

```text
[x] consume_inventory_item
[x] add_intake_item_from_inventory
```

---

## Implemented MCP Resources

```text
[x] grocery://inventory-consumption
```

Existing resources remain:

```text
[x] grocery://inventory
[x] grocery://intake/history
[x] grocery://intake/items
[x] grocery://intake-items
[x] grocery://food-waste
[x] grocery://food-waste/expired
```

---

## `consume_inventory_item` Behaviour

```text
[x] requires existing stock_id
[x] accepts quantity_used
[x] accepts servings_used
[x] requires at least one amount greater than zero
[x] rejects negative quantity_used
[x] rejects negative servings_used
[x] rejects quantity_used greater than current quantity
[x] rejects servings_used greater than current servings
[x] updates user_inventory.csv
[x] records user_inventory_consumption.csv event
[x] records before/after inventory state
[x] leaves depleted inventory row active with stock_status="out"
[x] does not create intake records
[x] does not create food waste records
[x] does not remove inventory row
```

---

## `add_intake_item_from_inventory` Behaviour

```text
[x] requires existing intake_id
[x] requires existing stock_id
[x] validates consumption amount before writing
[x] creates child intake item
[x] copies food_item from inventory row
[x] copies brand from inventory row
[x] copies category from inventory row
[x] copies unit from inventory row
[x] records quantity_used on intake item
[x] records servings_used on intake item
[x] deducts inventory
[x] records linked inventory consumption event
[x] links consumption event to intake_id
[x] links consumption event to intake_item_id
[x] records before/after inventory state
[x] does not create parent intake entry
[x] does not update parent meal-level totals
[x] does not create food waste record
[x] does not remove inventory row
```

---

## Ordinary Intake Behaviour

```text
[x] add_intake_item still requires existing intake_id
[x] add_intake_item accepts quantity_used and unit
[x] add_intake_item validates quantity_used
[x] add_intake_item validates servings_used
[x] add_intake_item validates nutrition estimates
[x] add_intake_item validates stock_id if supplied
[x] add_intake_item does not deduct inventory
[x] add_intake_item does not create inventory consumption event
```

---

## Inventory Status Behaviour

```text
[x] in_stock is the normal available status
[x] low indicates limited remaining stock
[x] very_low indicates nearly depleted stock
[x] out indicates no usable stock remains
[x] expired indicates expired food still physically present
[x] ok is rejected
[x] very low is rejected
[x] empty is rejected
[x] used is rejected
[x] removed is rejected
```

---

## Tests

```text
[x] tests/test_inventory_consumption.py passes
[x] tests/test_data_files.py passes
[x] tests/test_paths.py passes
[x] tests/test_mcp_resource_registration.py passes
[x] tests/test_resource_payloads.py passes
[x] tests/test_mcp_tool_registration.py passes
[x] full pytest suite passes
```

Useful commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_inventory_consumption.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_data_files.py tests/test_paths.py tests/test_mcp_resource_registration.py tests/test_resource_payloads.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tool_registration.py -q
.\.venv\Scripts\python.exe -m pytest
```

The full automated suite currently passes with `196 passed`.

---

## Manual MCP Inspector Testing

```text
[x] MCP Inspector lists consume_inventory_item
[x] MCP Inspector lists add_intake_item_from_inventory
[x] MCP Inspector lists grocery://inventory-consumption
[x] consume_inventory_item can reduce inventory quantity
[x] consume_inventory_item can reduce inventory servings
[x] consume_inventory_item creates a consumption event
[x] add_intake_item_from_inventory creates a child intake item
[x] add_intake_item_from_inventory reduces inventory
[x] add_intake_item_from_inventory creates a linked consumption event
[x] search_inventory confirms inventory changed
[x] search_intake confirms child intake item was created
[x] inventory-consumption resource shows event history
[x] over-consumption returns expected error
```

Adjust checkboxes if any manual items are still in progress.

---

## Curl Manual Checks

```text
[ ] initialize session
[ ] send initialized notification
[ ] list resources
[ ] read inventory
[ ] read inventory consumption
[ ] list tools
[ ] call consume_inventory_item
[ ] read inventory again
[ ] read inventory consumption again
[ ] call add_intake_item_from_inventory
[ ] search intake for the created child item
[ ] validation/error curl requests return expected errors
```

Curl testing can be completed after MCP Inspector validation.

---

## Explicitly Out of Scope

Version 1.3 does not add:

- automatic inventory deduction from ordinary `add_intake_item`
- automatic reversal of consumption
- consumption adjustment tools
- recipe-level consumption
- batch meal logging
- automatic shopping list generation
- meal planning intelligence
- restock recommendation intelligence
- waste pattern analysis automation

---

## Final Completion Statement

Version 1.3 is complete when controlled inventory consumption is implemented, tested, exposed through MCP tools/resources, and documented.

The version should close with the project following this architecture principle:

```text
CSV files
    ↓
core service functions
    ↓
thin MCP resources/tools
    ↓
MCP-compatible client
```

Version 1.3 strengthens the data foundation by separating:

```text
Inventory state
Intake records
Inventory consumption events
Food waste events
```
