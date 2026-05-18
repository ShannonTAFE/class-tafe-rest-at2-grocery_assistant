# Version 1.4 Working Notes — Core Refactor and Batch Meal Planning

## Version Theme

Version 1.4 is being developed in two major stages:

```text
Version 1.4A — Core service refactor
Version 1.4B — Batch meal logging tools
Version 1.4C — Batch inventory-linked meal logging
```

The refactor stage was completed first because Version 1.4 batch workflows will be more complex than the previous single-action tools.

Version 1.4 introduces workflows that may eventually coordinate:

```text
user_intake_history.csv
user_intake_items.csv
user_inventory.csv
user_inventory_consumption.csv
```

Because of this, the project needed a cleaner service structure before adding more orchestration logic.

---

# Version 1.4A — Core Service Refactor

## Goal

The goal of Version 1.4A was to reduce the size and complexity of `grocery_service.py` without changing public behaviour.

The refactor focused on extracting shared helpers, schemas, constants, validation rules, and transaction-like save helpers into focused modules.

The main rule was:

> Refactor structure first. Do not change tool behaviour.

---

## Why the Refactor Was Needed

By the end of Version 1.3, `grocery_service.py` contained:

- CSV schemas
- valid domain values
- generic service helpers
- inventory rules
- intake validation
- consumption validation
- food waste record construction
- relationship helpers
- multi-file save logic
- public inventory tools
- public intake tools
- public consumption tools
- resource read helpers

This was manageable for Versions 1.0–1.3, but Version 1.4 batch workflows would make the file too difficult to maintain.

The refactor prepares the codebase for batch workflows while preserving the existing architecture:

```text
CSV files
    ↓
core service functions
    ↓
thin MCP tools/resources
    ↓
MCP-compatible client
```

---

# Completed Refactor Modules

## `schemas.py`

Extracted CSV column definitions:

```text
INVENTORY_COLUMNS
FOOD_WASTE_COLUMNS
INTAKE_HISTORY_COLUMNS
INTAKE_ITEMS_COLUMNS
INVENTORY_CONSUMPTION_COLUMNS
```

Purpose:

- centralise data contracts
- make schema reuse easier
- prepare for future batch workflow tests

---

## `constants.py`

Extracted domain vocabulary constants:

```text
VALID_STOCK_STATUSES
VALID_REMOVAL_TYPES
WASTE_REMOVAL_TYPES
VALID_TRACKING_CONFIDENCE
VALID_MEAL_TYPES
VALID_CONSUMPTION_TYPES
VALID_CONFIDENCE_LEVELS
VALID_YES_NO_UNKNOWN
VALID_FINISHED_STATUSES
```

Purpose:

- keep domain choices in one file
- avoid duplicating valid values across future services
- preserve Version 1.3 stock status vocabulary

---

## `service_utils.py`

Extracted shared service helpers:

```text
today_iso
to_float
validate_choice
df_to_records
to_json
safe_text_series
normalise_search_limit
optional_clean_text
contains_query_mask
exact_text_mask
```

Purpose:

- keep reusable service utilities separate from workflow logic
- support future query and batch modules
- reduce helper noise in `grocery_service.py`

---

## `csv_store.py`

Added future-facing CSV access wrappers.

This module is intended to eventually centralise CSV reads such as:

```text
read_inventory
read_food_waste
read_intake_history
read_intake_items
read_inventory_consumption
```

and write-oriented wrappers such as:

```text
read_inventory_for_write
read_food_waste_for_write
read_intake_history_for_write
read_intake_items_for_write
read_inventory_consumption_for_write
```

Important compatibility decision:

Some read wrappers were restored in `grocery_service.py` during the refactor because existing tests were monkeypatching path constants on `grocery_service`.

The project now has test support to patch paths across multiple core modules, which will allow future service splitting to continue safely.

---

## `inventory_rules.py`

Extracted inventory-specific rule helpers:

```text
infer_stock_status
validate_inventory_stock_consistency
find_possible_inventory_duplicates
validate_stock_status
```

Purpose:

- keep inventory state rules separate from inventory write workflows
- support both inventory tools and consumption workflows
- preserve canonical Version 1.3 stock status behaviour

---

## `transaction_helpers.py`

Extracted related CSV save logic:

```text
save_related_csv_updates
```

Purpose:

- support transaction-like multi-file workflows
- preserve best-effort rollback behaviour
- prepare for Version 1.4 batch meal operations

This helper does not replace real database transactions, but it reduces the chance of related CSV files being left out of sync.

---

## `relationship_helpers.py`

Extracted DataFrame-based relationship helpers:

```text
id_exists
require_existing_id
```

Purpose:

- support relationship validation without tying helpers to one service module
- avoid circular imports
- prepare for future service splitting

Path-dependent relationship helpers remain in `grocery_service.py` for now.

---

## `consumption_helpers.py`

Extracted controlled consumption helper logic:

```text
validate_consumption_amounts
calculate_inventory_after_consumption
apply_inventory_consumption_to_df
build_inventory_consumption_record
build_intake_item_from_inventory_row
```

Purpose:

- separate consumption calculation/build logic from public write workflows
- prepare for batch inventory-linked meal logging
- preserve Version 1.3 controlled consumption behaviour

The public workflows remain in `grocery_service.py` for now:

```text
consume_inventory_item
add_intake_item_from_inventory
```

---

## `waste_helpers.py`

Extracted food waste helper logic:

```text
should_create_food_waste_record
build_food_waste_record
```

Purpose:

- separate food waste record construction from inventory removal
- keep `remove_inventory_item` focused on orchestration
- prepare for future waste pattern analysis

The public workflow remains in `grocery_service.py`:

```text
remove_inventory_item
```

---

## `intake_helpers.py`

Extracted intake validation helpers:

```text
INTAKE_ENTRY_NUMERIC_FIELDS
INTAKE_ITEM_NUMERIC_FIELDS
clean_and_validate_intake_entry_fields
clean_and_validate_intake_item_fields
validate_intake_entry_updates
validate_intake_item_updates
```

Purpose:

- reduce repeated validation logic in intake write functions
- prepare for batch meal creation
- preserve the Version 1.2 parent-child safety foundation

Refactored public functions now use these helpers:

```text
add_intake_entry
update_intake_entry
add_intake_item
update_intake_item
```

---

# Test Refactor Progress

## Centralised Grocery CSV Path Patching

Tests were updated to use central path patching through `tests/conftest.py`.

The new fixture patches temporary CSV paths across:

```text
grocery_service
csv_store
future inventory_service
future intake_service
future intake_query_service
future consumption_service
future waste_service
future batch_meal_service
```

This prevents tests from accidentally writing to one module’s temp CSV path while reading from another module’s real project CSV path.

---

## New Refactor Contract Tests

Added:

```text
tests/test_core_refactor_contracts.py
```

This verifies:

- `grocery_service.py` still exports expected public functions
- extracted helper modules import cleanly
- path patching applies to both `grocery_service` and `csv_store`
- future service modules can be absent without breaking the fixture

---

## Updated Existing Tests

Updated older local fixtures in:

```text
tests/test_v1_1_additional_coverage.py
tests/test_v1_1_write_foundation.py
```

These now delegate to the central `grocery_csv_paths` fixture instead of manually monkeypatching only `grocery_service`.

---

# Windows Pytest Temp Folder Issue

During the refactor, `.pytest-tmp` and `.pytest_cache` became locked on Windows.

Current workaround:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp-2 -p no:cacheprovider
```

Project ignore entries were added or confirmed:

```gitignore
.pytest_cache/
.pytest-tmp/
.pytest-tmp-*/
```

Before finalising the Version 1.4 branch:

- retry cleanup after restarting Windows
- use elevated PowerShell if needed
- continue using the alternate `--basetemp` command if the folders remain locked
- ensure pytest temp/cache folders are not tracked by git

---

# Current Refactor Boundary

The refactor intentionally stops short of moving all public service functions into separate service modules.

Still in `grocery_service.py` for now:

```text
read_inventory
read_food_waste
read_intake_history
read_intake_items
read_inventory_consumption

list_inventory_items
find_inventory_item
search_inventory
add_inventory_item
update_inventory_item
remove_inventory_item

list_intake_history
list_intake_items
get_recent_intake
get_daily_intake_summary
search_intake

add_intake_entry
update_intake_entry
add_intake_item
update_intake_item
remove_intake_item
remove_intake_entry

list_inventory_consumption
consume_inventory_item
add_intake_item_from_inventory
```

Reason:

> These functions are public workflow functions or path-dependent functions. Moving them should be done later with the new test path fixture in place.

---

# Version 1.4A Status

Version 1.4A is now substantially complete.

Completed:

```text
[x] Extract schemas
[x] Extract constants
[x] Extract service utilities
[x] Add CSV store module
[x] Extract inventory rules
[x] Extract transaction helper
[x] Extract DataFrame relationship helpers
[x] Extract consumption helpers
[x] Extract food waste helpers
[x] Extract intake validation helpers
[x] Centralise test CSV path patching
[x] Add refactor contract tests
[x] Preserve existing public tool behaviour
[x] Full test suite passes with Windows temp workaround
```

Deferred:

```text
[ ] Move public inventory functions to inventory_service.py
[ ] Move public intake query functions to intake_query_service.py
[ ] Move public intake write functions to intake_service.py
[ ] Move public consumption workflows to consumption_service.py
[ ] Turn grocery_service.py into a pure facade
```

These are no longer blockers for Version 1.4 batch tool development because the most useful helper logic has already been extracted.

---

# Version 1.4B — Batch Meal Logging Completion

## Goal

Version 1.4B added a safe batch intake workflow:

```text
add_meal_with_items
```

The goal was to create one parent intake entry and multiple child intake item rows in one controlled operation.

This gives agents a cleaner way to log meals with multiple components without calling multiple single-row intake tools manually.

---

## Implemented Workflow

```text
meal_data + items
    ↓
validate parent meal data
    ↓
validate every child intake item
    ↓
validate supplied stock_id references, if any
    ↓
generate parent intake_id
    ↓
generate child intake_item_id values
    ↓
build all new rows in memory
    ↓
save intake history and intake items together
    ↓
return created parent and children
```

---

## Writes To

```text
user_intake_history.csv
user_intake_items.csv
```

---

## Does Not Write To

```text
user_inventory.csv
user_inventory_consumption.csv
user_food_waste.csv
```

---

## Important Behaviour Rules

```text
If the parent meal is invalid, no child items are created.
If any child item is invalid, the parent meal is not created.
All child items link to the created parent intake_id.
All input validates before writing.
The workflow uses transaction-like related CSV saving.
The workflow does not deduct inventory.
The workflow does not create inventory consumption records.
The workflow does not create food waste records.
```

---

## Stock ID Boundary

Version 1.4B allows optional `stock_id` values on child intake items only as references.

```text
stock_id in add_meal_with_items = possible relationship/reference
stock_id in add_meal_with_items != inventory deduction
```

If a `stock_id` is supplied, it is validated against inventory, but the inventory row is not changed.

This preserves the Version 1.3 rule that ordinary intake logging does not silently reduce inventory.

---

## MCP Tool Exposure

The service function is exposed through an MCP tool:

```text
add_meal_with_items
```

The MCP wrapper should remain thin.

Business rules belong in the service layer, not the MCP tool wrapper.

---

## Version 1.4B Status

Completed:

```text
[x] Implement batch meal service function
[x] Validate parent meal data
[x] Validate child intake items
[x] Reject empty child item lists
[x] Reject unsupported fields
[x] Validate supplied stock_id values
[x] Generate parent and child IDs
[x] Save intake history and intake items together
[x] Return created parent and children
[x] Return explicit non-deduction flags
[x] Add service-layer tests
[x] Register MCP tool
[x] Confirm MCP Inspector workflow
[x] Full pytest suite passes
```

Deferred:

```text
[ ] Inventory-linked batch meal logging
[ ] Aggregate duplicate stock_id validation across a batch
[ ] Batch inventory deduction
[ ] Linked consumption event creation for each child item
[ ] Meal aliases
[ ] Meal templates
[ ] Learning tools
[ ] Recipe support
[ ] Automatic nutrition rollups
```

---

# Version 1.4C — Batch Inventory-Linked Meal Logging Direction

Version 1.4C should build on Version 1.4B by adding an explicit inventory-linked batch workflow.

Candidate tool:

```text
add_meal_with_inventory_items
```

Goal:

> Create one parent intake entry, multiple child intake items, deduct selected inventory items, and create linked inventory consumption events.

This tool may write to:

```text
user_intake_history.csv
user_intake_items.csv
user_inventory.csv
user_inventory_consumption.csv
```

It should not create food waste records unless a future workflow explicitly includes waste handling.

---

## Version 1.4C Design Rules

```text
All inputs must validate before any write.
Inventory deduction must be explicit.
Duplicate stock_id usage in one batch must be checked as an aggregate.
Inventory must not be deducted unless the explicit inventory-linked batch tool is used.
Each consumption event must link to the created intake_id and intake_item_id.
No consumption event should be created unless the matching intake item is created.
No parent meal should be created if inventory deduction validation fails.
Inventory before/after state must be recorded for every deduction.
```

---

## Key Question Before Implementation

Before writing Version 1.4C code, decide the request shape.

Important open questions:

```text
Should consumption_type be batch-level, item-level, or both?
Should tracking_confidence be batch-level, item-level, or both?
Should food_item be copied from inventory, supplied by the user, or both?
How should duplicate stock_id values be aggregated?
Should quantity unit conversion be rejected for now?
Should blank stock_id be allowed in an inventory-linked batch tool?
```

Recommended starting point:

```text
Require stock_id for every inventory-linked child item.
Copy food_item, brand, category, and unit from inventory.
Allow amount_eaten and nutrition estimates as child item fields.
Require quantity_used and/or servings_used greater than zero.
Do not support unit conversion in Version 1.4C.
Aggregate duplicate stock_id usage before validating availability.
```

---

## Recommended First Version 1.4C Development Step

Begin with a planning and test-design pass before writing service code:

```text
1. Finalise add_meal_with_inventory_items request shape.
2. Write service-layer tests for successful batch inventory-linked meal logging.
3. Write no-partial-write tests for invalid child items and invalid inventory use.
4. Write aggregate duplicate stock_id tests.
5. Implement the service only after the validation expectations are clear.
```

---

# Version 1.4 Closeout Statement

Version 1.4A stabilised the core service structure.

Version 1.4B added a safe batch meal intake workflow.

The project is now ready to begin Version 1.4C, which should add explicit inventory-linked batch meal logging without weakening the existing intake-only boundary.
