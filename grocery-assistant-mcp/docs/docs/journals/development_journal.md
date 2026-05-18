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
