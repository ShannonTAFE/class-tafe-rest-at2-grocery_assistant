# Grocery Assistant MCP Roadmap

## Purpose

This roadmap documents the planned progression of the Grocery Assistant MCP project from a read-only MCP server into a safe write-capable assistant and eventually a more intelligent grocery planning system.

The project is built around three core areas:

```text
Inventory = what the user has, had, or wants to remember for planning
Intake = what the user ate
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
Edit/delete tools for intake and relationship cleanup.

Version 1.3:
Controlled inventory consumption tools.

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

## Deferred

```text
automatic inventory deduction
consume_inventory_item
add_meal_with_items
intake edit/delete tools
shopping automation
advanced waste analysis
```

## Key Decisions

- Intake logging does not automatically reduce inventory.
- Intake items must link to a valid parent intake entry.
- Intake item `stock_id` is optional.
- Waste records are created through inventory removal only when the removal type is waste-related.
- MCP tool wrappers remain thin.
- Business logic stays in the service layer.

---

# Version 1.2 — Relationship Editing and Cleanup

## Goal

Add safe editing and removal for intake parent-child records.

## Possible Tools

```text
update_intake_entry
update_intake_item
remove_intake_item
remove_intake_entry
```

## Main Design Rule

Start conservatively. If a parent meal has child items, block parent removal until the child items are handled.

---

# Version 1.3 — Controlled Inventory Consumption

## Goal

Add explicit tools for reducing inventory.

## Possible Tool

```text
consume_inventory_item
```

## Key Rule

Inventory consumption should be separate from intake logging until the relationship is safe and well tested.

---

# Version 1.4 — Batch Meal Logging

## Goal

Support higher-level meal creation workflows.

## Possible Tool

```text
add_meal_with_items
```

## Risk

This version introduces multi-file writes. The project will need a clear strategy for validation, partial write prevention, and cleanup.

---

# Version 1.5 — Planning Intelligence

## Goal

Use inventory, intake, and waste records for smarter recommendations.

## Possible Capabilities

```text
suggest_restock_items
suggest_meals_from_inventory
suggest_use_soon_items
review_waste_patterns
review_intake_patterns
create_shopping_candidates
```

---

# Long-Term Design Principles

## Keep Writes Explicit

Avoid tools that silently update multiple records unless the behaviour is clearly documented and tested.

## Keep Tool Wrappers Thin

MCP tools should describe inputs and call service functions. They should not duplicate business logic.

## Keep Helpers Generic

Generic helper files should contain reusable validation and CSV helpers. Domain rules should stay in the service layer.

## Use Consistent IDs

Recommended ID style:

```text
inv_001
intake_001
intake_item_001
waste_001
```

## Document Deferred Ideas

Future ideas should be captured in roadmap documentation rather than added into the current version too early.
