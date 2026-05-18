# Version 1.4 Closeout Checklist

## Version summary

Version 1.4 completes the transition from single-record workflows to safe batch meal workflows.

Completed stages:

```text
Version 1.4A — Core service refactor
Version 1.4B — Intake-only batch meal logging
Version 1.4C — Inventory-linked batch meal logging
```

## Required final checks

```text
[ ] Full pytest suite passes.
[ ] Version 1.4B service tests pass.
[ ] Version 1.4C service tests pass.
[ ] MCP tool registration tests pass.
[ ] MCP resource registration tests pass.
[ ] MCP Inspector connects to streamable HTTP server.
[ ] tools/list shows add_meal_with_items.
[ ] tools/list shows add_meal_with_inventory_items.
[ ] resources/list shows expected grocery resources.
[ ] Fresh empty dataset curl workflow succeeds.
[ ] Curl responses are saved as readable .json files.
[ ] add_meal_with_items creates parent and child intake rows.
[ ] add_meal_with_items does not deduct inventory.
[ ] add_meal_with_items does not create inventory consumption records.
[ ] add_meal_with_inventory_items creates parent and child intake rows.
[ ] add_meal_with_inventory_items deducts explicit inventory items.
[ ] add_meal_with_inventory_items creates linked inventory consumption records.
[ ] Food waste remains unchanged during normal meal logging.
[ ] Validation/error curl requests fail safely.
[ ] Documentation reflects final Version 1.4 behaviour.
```

## Version 1.4 completion statement

Version 1.4 can be considered complete when the test suite passes and the fresh empty dataset MCP workflow confirms both batch meal paths:

```text
add_meal_with_items
add_meal_with_inventory_items
```

No future planning document should describe Version 1.4 as only planned once this checklist is complete.
