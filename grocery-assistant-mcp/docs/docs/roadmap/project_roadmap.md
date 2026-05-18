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

Main principle:

```text
Build safe, explicit write foundations before adding automation.
```

---

# Version Timeline

```text
Version 1.0 — Read-only MCP grocery assistant
Version 1.1 — Safe write tools for inventory, intake, and waste
Version 1.2 — Relationship-safe intake search, editing, and cleanup
Version 1.3 — Controlled inventory consumption tools and consumption event logging
Version 1.4 — Batch meal logging and transaction-like workflows
Version 1.5 — Planning intelligence and suggestion workflows
```

---

# Version 1.0 — Read-Only MCP Grocery Assistant

Goal:

```text
Expose grocery data safely as read-only MCP resources and summary tools.
```

Completed capabilities:

- read inventory
- read intake history
- read intake items
- search inventory
- review recent intake
- summarise daily intake
- expose prompts for common assistant workflows
- test resources and tools with MCP Inspector and curl

---

# Version 1.1 — Safe Write Foundation

Goal:

```text
Add controlled write tools without hidden side effects.
```

Completed capabilities:

- add inventory items
- update inventory items
- remove inventory items
- add parent intake entries
- add child intake items
- food waste handling through explicit removal workflows

Key decisions:

- Intake logging does not automatically reduce inventory.
- Intake items must link to a valid parent intake entry.
- Intake item `stock_id` is optional.
- Waste records are created only when removal type is waste-related.
- MCP tool wrappers remain thin.
- Business logic stays in the service layer.

---

# Version 1.2 — Intake Relationship Editing and Cleanup

Goal:

```text
Safely search, update, and remove parent/child intake records.
```

Completed capabilities:

- search intake parent entries and child items
- update parent intake entries
- update child intake items
- remove child intake items
- block parent removal while child items exist
- avoid cascade deletion

---

# Version 1.3 — Controlled Inventory Consumption

Goal:

```text
Allow explicit inventory deduction while preserving an event history.
```

Completed capabilities:

- consume inventory without creating intake rows
- create intake items from inventory
- reduce quantity and/or servings
- record inventory consumption events
- link consumption events to intake items
- expose inventory consumption as a resource

Key decision:

```text
Ordinary intake logging still does not silently deduct inventory.
```

---

# Version 1.4 — Batch Meal Logging and Transaction-Like Workflows

Status:

```text
Current closeout baseline.
```

Goal:

```text
Create safe batch workflows that coordinate parent meals, child items, and optionally inventory consumption.
```

Completed stages:

```text
Version 1.4A — Core service refactor
Version 1.4B — Intake-only batch meal logging
Version 1.4C — Inventory-linked batch meal logging
```

Completed tools:

```text
add_meal_with_items
add_meal_with_inventory_items
```

Version 1.4B rule:

```text
Create parent and child intake records without inventory deduction.
```

Version 1.4C rule:

```text
Deduct inventory only when the request explicitly uses inventory-linked items.
```

Non-goals:

- no automatic meal alias learning
- no recipe system
- no shopping list generation
- no automatic inventory deduction from a meal name alone
- no hidden food waste creation during normal meal logging

---

# Version 1.5 — Planning Intelligence

Possible goals:

- meal suggestions from available inventory
- restock suggestions
- low-stock review
- food waste pattern review
- simple shopping list draft support
- meal planning prompts based on inventory and recent intake

Safety principle:

```text
Suggestions can be intelligent, but writes should remain explicit.
```

Inventory-changing actions should still route through tested tools.
