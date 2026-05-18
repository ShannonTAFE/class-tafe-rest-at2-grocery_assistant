# Grocery Assistant MCP Roadmap

## Purpose

This roadmap documents the planned progression of the Grocery Assistant MCP project from a read-only MCP server into a safe write-capable assistant and eventually a more intelligent grocery planning system.

The project is built around four core areas:

```text
Inventory = what the user has, had, or wants to remember for planning
Intake = what the user ate
Inventory consumption = why tracked inventory quantities changed
Waste = food that was discarded, spoiled, expired, unused, or otherwise wasted
```

---

# Strategic Version Plan

```text
Version 1.0:
Read-only MCP grocery assistant.

Version 1.1:
Safe write tools for inventory, intake, and waste.

Version 1.2:
Relationship-safe intake search, editing, and cleanup.

Version 1.3:
Controlled inventory consumption tools and consumption event logging.

Version 1.4:
Batch meal logging and transaction-like workflows.

Version 1.5:
Planning intelligence: restock suggestions, meal suggestions, waste pattern review.
```

The main project principle is:

> Build safe, explicit write foundations before adding automation.

---

# Version 1.0 — Read-Only MCP Grocery Assistant

## Goal

Establish the MCP server structure and expose grocery data safely as read-only resources and summary tools.

## Main Capabilities

- read inventory
- read intake history
- read intake items
- search inventory
- review recent intake
- summarise daily intake
- expose prompts for common assistant workflows
- test resources and tools using MCP Inspector and curl

---

# Version 1.1 — Safe Write Foundation

## Goal

Add controlled write tools without hidden side effects.

## Included

```text
search_inventory
add_inventory_item
update_inventory_item
remove_inventory_item
get_recent_intake
get_daily_intake_summary
add_intake_entry
add_intake_item
food waste resources
```

## Key Decisions

- Intake logging does not automatically reduce inventory.
- Intake items must link to a valid parent intake entry.
- Intake item `stock_id` is optional.
- Waste records are created through inventory removal only when the removal type is waste-related.
- MCP tool wrappers remain thin.
- Business logic stays in the service layer.

---

# Version 1.2 — Intake Relationship Editing and Cleanup

## Status

Complete.

## Goal

Add safe search, editing, and removal tools for intake records while preserving the relationship between parent meal entries and child ingredient/component rows.

## Included

```text
search_intake
update_intake_entry
update_intake_item
remove_intake_item
remove_intake_entry
parent-child relationship checks
parent removal blocking when child items exist
service-layer tests
MCP Inspector validation
```

## Main Workflow

```text
search_intake
    ↓
inspect intake_id / intake_item_id
    ↓
update_intake_entry or update_intake_item
    ↓
remove_intake_item if needed
    ↓
remove_intake_entry only when no child items remain
```

## Design Notes

Version 1.2 avoids cascade deletion. Parent intake entries cannot be removed while child intake items still exist.

This is intentionally conservative. It prevents orphaned records and avoids accidental loss of ingredient/component data.

---

# Version 1.3 — Controlled Inventory Consumption

## Status

Implemented / finalising manual validation and documentation.

## Goal

Add explicit tools for reducing inventory and recording consumption events.

## Included

```text
consume_inventory_item
add_intake_item_from_inventory
user_inventory_consumption.csv
grocery://inventory-consumption
quantity_used and unit on intake items
canonical stock_status vocabulary
service-layer tests
MCP Inspector validation
```

## Main Workflows

Inventory-only consumption:

```text
search_inventory
    ↓
consume_inventory_item
    ↓
inventory is updated
    ↓
consumption event is recorded
```

Intake-linked consumption:

```text
add_intake_entry
    ↓
add_intake_item_from_inventory
    ↓
child intake item is created
    ↓
inventory is updated
    ↓
linked consumption event is recorded
```

## Key Decisions

- Ordinary `add_intake_item` does not automatically deduct inventory.
- Consumption does not create food waste records.
- Depleted inventory remains active with `stock_status="out"`.
- Consumption events are recorded separately from intake rows.
- Intake items now store `quantity_used`, `unit`, and `servings_used`.

## Deferred

```text
automatic consumption reversal
adjust consumption event
batch meal logging
recipe-level inventory consumption
shopping list generation
meal planning intelligence
restock suggestions
waste pattern analysis
```

---

# Version 1.4 — Batch Meal Logging

## Goal

Support higher-level meal creation workflows.

Possible tools:

```text
add_meal_with_items
add_intake_entry_with_items
add_meal_with_inventory_items
```

## Risk

This version introduces more complex multi-file writes. The project will need a clear strategy for:

- validating all data before writing
- preventing partial writes
- handling rollback or cleanup
- returning clear error messages
- avoiding accidental inventory deduction

Version 1.3 prepares for this by adding inventory consumption event logging and best-effort related CSV save behaviour.

---

# Version 1.5 — Planning Intelligence

## Goal

Use inventory, intake, consumption, and waste records for smarter recommendations.

Possible capabilities:

```text
suggest_restock_items
suggest_meals_from_inventory
suggest_use_soon_items
review_waste_patterns
review_consumption_patterns
review_intake_patterns
create_shopping_candidates
summarise_grocery_state
```

Planning intelligence should begin as read-only analysis and prompts before becoming write-heavy automation.

---

# Long-Term Design Principles

## Keep Writes Explicit

Avoid tools that silently update multiple records unless the behaviour is clearly documented and tested.

## Keep Tool Wrappers Thin

MCP tools should describe inputs and call service functions. They should not duplicate business logic.

## Keep Helpers Generic

Generic helper files should contain reusable validation and CSV helpers. Domain rules should stay in the service layer.

## Separate State from Events

Inventory is current state. Consumption and waste are events. Intake is eating history.

## Use Consistent IDs

Recommended ID style:

```text
inv_001
intake_001
intake_item_001
consumption_001
waste_001
```

## Document Deferred Ideas

Future ideas should be captured in roadmap documentation rather than added into the current version too early.
