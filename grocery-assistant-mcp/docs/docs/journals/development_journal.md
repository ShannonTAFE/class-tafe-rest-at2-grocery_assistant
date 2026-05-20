# Development Journal

## Version 1.1

Focus:

```text
Safe write foundation.
```

Key notes:

- Added controlled write tools for inventory and intake.
- Clarified that MCP tool wrappers should stay thin.
- Kept business logic in the service layer.
- Confirmed hunger fields should be sent as strings in curl requests.
- Used MCP Inspector and curl to validate Streamable HTTP behaviour.

## Version 1.2

Focus:

```text
Relationship-safe intake editing and cleanup.
```

Key notes:

- Added search/update/remove workflows for intake parent and child records.
- Preserved parent-child safety by blocking parent removal while child items exist.
- Avoided cascade deletion.
- Strengthened service-layer tests.

## Version 1.3

Focus:

```text
Controlled inventory consumption.
```

Key notes:

- Added explicit inventory consumption without intake logging.
- Added inventory-linked intake item workflow.
- Added inventory consumption event logging.
- Preserved the rule that ordinary intake logging does not deduct inventory.
- Exposed inventory consumption as a resource.

## Version 1.4

Focus:

```text
Batch meal logging and transaction-like workflows.
```

Key notes:

- Refactored the service layer before adding more complex workflows.
- Added intake-only batch meal logging through `add_meal_with_items`.
- Added inventory-linked batch meal logging through `add_meal_with_inventory_items`.
- Confirmed inventory deduction should occur only for explicitly selected inventory items.
- Reset curl testing around a clean empty dataset and JSON response files.

---

## Version 1.5A Closeout

Version 1.5A introduced the first read-only planning signal foundation for the Grocery Assistant MCP project.

The main output was `review_planning_context`, an MCP-facing tool that reads existing grocery records and returns structured planning signals, data-quality notes, records-checked metadata, and safety metadata.

A key architectural decision was to separate source records from derived planning signals. CSV files remain the source of truth, while the planning layer derives temporary context for agent reasoning.

The version intentionally avoided meal recommendations, shopping list generation, preference learning, and automatic write actions. This protects the project from moving into recommendation logic before the signal contract is stable.

MCP Inspector confirmed the tool is visible and callable. Tests now protect the response contract, read-only behaviour, safety metadata, and the rule that `recommendations` remains empty in Version 1.5A.

Version 1.5A is now closed and ready to support Version 1.5B.

## Version 1.5B

...missed doc updates...


## Version 1.5C — Signal-Based Meal Suggestion Drafts

Implemented a read-only `draft_meal_suggestions` feature that creates basic meal opportunity drafts from inventory signals.

Key additions:
- availability/use-soon signal interpretation
- simple food role inference
- basic meal templates
- gap-tolerant suggestions
- priority and confidence scoring
- MCP tool registration
- tests for empty inventory, use-soon items, low-stock gaps, out-of-stock exclusion, expired exclusion, missing expiry data, and max suggestion limits

This version intentionally avoids full recipe generation, nutrition optimisation, shopping-list writes, or automatic restock decisions.