# Development Journal — Version 1.3

## Version Theme

Version 1.3 focused on controlled inventory consumption and a stronger dataset foundation.

The main goal was to allow inventory to be reduced safely without turning ordinary intake logging into hidden automation.

Version 1.3 introduced a clear relationship between:

```text
user_inventory.csv
    stock_id
        ↓
user_inventory_consumption.csv
    stock_id
```

and, for linked intake consumption:

```text
user_intake_history.csv
    intake_id
        ↓
user_intake_items.csv
    intake_id + stock_id
        ↓
user_inventory_consumption.csv
    intake_id + intake_item_id + stock_id
```

---

## Planning

- Reviewed Version 1.2 final documentation and confirmed that inventory consumption was intentionally deferred.
- Defined Version 1.3 as "Controlled Inventory Consumption".
- Agreed that existing `add_intake_item` should not automatically deduct inventory.
- Decided to add explicit consumption tools rather than hidden side effects.
- Chose to build a shared inventory deduction path used by both consumption workflows.
- Identified that quantity-based consumption needed stronger intake item fields.
- Refactored the dataset foundation before adding more roadmap complexity.

---

## Dataset Foundation Decisions

Version 1.3 introduced a new CSV file:

```text
user_inventory_consumption.csv
```

This file records inventory usage events and explains why inventory quantities changed.

Version 1.3 also updated `user_intake_items.csv` to include:

```text
quantity_used
unit
```

This gives intake item rows both human-readable and machine-readable consumption detail.

Example:

```text
amount_eaten = "500 ml"
quantity_used = 500
unit = "ml"
servings_used = 0
```

Version 1.3 also cleaned up inventory stock status values.

Canonical statuses:

```text
in_stock
low
very_low
out
expired
```

Removed earlier/example statuses:

```text
ok
very low
empty
used
removed
```

---

## Implementation

Implemented or updated service-layer behaviour for:

- validating consumption amounts
- calculating inventory state after consumption
- applying inventory consumption to an inventory DataFrame
- building inventory consumption event records
- saving related CSV updates with best-effort rollback
- consuming inventory without intake logging
- creating intake items from inventory and consuming stock
- listing inventory consumption records
- reading inventory consumption records

Implemented new or updated MCP behaviour for:

- `consume_inventory_item`
- `add_intake_item_from_inventory`
- `grocery://inventory-consumption`

Updated existing intake service behaviour so intake item records can store:

- `quantity_used`
- `unit`
- `servings_used`

Updated existing inventory behaviour to use the Version 1.3 stock vocabulary.

---

## Controlled Consumption Design

Version 1.3 includes two controlled consumption workflows.

### Inventory-only consumption

```text
consume_inventory_item
    ↓
user_inventory.csv updated
    ↓
user_inventory_consumption.csv event recorded
```

Use this when inventory changed but no intake item should be created.

Example:

```text
"I drank 500 ml of milk."
```

### Intake-linked consumption

```text
add_intake_item_from_inventory
    ↓
user_intake_items.csv child row created
    ↓
user_inventory.csv updated
    ↓
user_inventory_consumption.csv linked event recorded
```

Use this when a tracked inventory item was eaten or used as part of an existing intake entry.

Example:

```text
"Add 100g chicken breast from inventory to dinner."
```

---

## Important Boundaries

Version 1.3 intentionally keeps these behaviours out of scope:

- ordinary `add_intake_item` does not deduct inventory
- removing an intake item does not restore inventory
- updating an intake item does not automatically adjust inventory
- consumption does not create food waste records
- parent meal totals are not automatically recalculated
- batch meal logging is not implemented
- recipe-level inventory deduction is not implemented

These boundaries keep the system explicit and easier to debug.

---

## Challenges

### Avoiding hidden side effects

The first major design question was whether existing intake tools should deduct inventory when `stock_id` is present.

The decision was no.

A normal intake item may represent restaurant food, takeaway food, shared food, leftovers, or historical estimates. The presence of a `stock_id` should not silently mutate inventory.

### Multi-file writes

The linked workflow writes to multiple files:

```text
user_inventory.csv
user_intake_items.csv
user_inventory_consumption.csv
```

This required careful validation before saving and a best-effort rollback helper for related CSV updates.

This does not replace a real database transaction, but it reduces the risk of leaving related CSVs out of sync during early CSV-based development.

### Dataset vocabulary cleanup

The seed data and older tests used `stock_status="ok"`, but the project moved to a clearer vocabulary using `in_stock`.

Because the project is still early and data is example-only, the better decision was to refactor the schema instead of supporting legacy aliases.

### Quantity and unit tracking

Version 1.3 introduced quantity-based inventory consumption, such as `500 ml`.

The old intake item schema could store `servings_used` but not the actual quantity and unit used. This was fixed by adding `quantity_used` and `unit` to `user_intake_items.csv`.

---

## Testing

Service-layer tests were added or updated for:

- inventory-only consumption
- linked intake/inventory consumption
- inventory consumption event creation
- before/after inventory state tracking
- quantity-based consumption
- serving-based consumption
- exact depletion to `out`
- over-consumption rejection
- invalid stock ID rejection
- invalid intake ID rejection
- invalid confidence/status validation
- no unwanted intake writes during inventory-only consumption
- no unwanted consumption event writes on invalid linked workflows
- canonical stock status validation
- intake item quantity/unit schema support

Resource and registration tests were updated for:

- `grocery://inventory-consumption`
- `consume_inventory_item`
- `add_intake_item_from_inventory`
- `user_inventory_consumption.csv`

The full pytest suite passed after the Version 1.3 schema refactor.

MCP Inspector testing was used to confirm that the tools and resources were exposed and callable through the MCP layer.

Curl testing was used or reserved as additional manual HTTP validation.

---

## Version Control Notes

Version 1.3 should be committed as a focused feature update.

Suggested commit message:

```text
feat: add controlled inventory consumption workflows
```

Suggested branch name:

```text
feature/version-1.3-controlled-consumption
```

Possible commit split:

```text
1. refactor: update v1.3 CSV schemas and stock status vocabulary
2. feat: add inventory consumption event logging
3. feat: expose controlled consumption tools and resource
4. docs: update documentation for version 1.3
```

---

## Reflection

Version 1.3 is an important architectural step because it introduces controlled multi-file workflows without making the assistant overly automatic.

The project now has separate concepts for:

```text
Inventory state
Intake records
Inventory consumption events
Food waste events
```

That separation is more robust than simply reducing inventory inside intake logging.

The most important design decision was adding `user_inventory_consumption.csv`. This makes stock changes explainable and prepares the project for future features such as undo, adjustment, recipe consumption, restock analysis, and planning intelligence.

---

## Version 1.3 Closeout Note

Version 1.3 is feature complete when the controlled consumption tools, schema updates, event logging, MCP resources, and tests are complete.

The version adds:

- `consume_inventory_item`
- `add_intake_item_from_inventory`
- `user_inventory_consumption.csv`
- `grocery://inventory-consumption`
- `quantity_used` and `unit` on intake items
- canonical inventory stock statuses

The project now supports explicit inventory reduction while preserving the safety boundaries from earlier versions.

The next major development direction is Version 1.4, focused on batch meal logging and transaction-like workflows.
