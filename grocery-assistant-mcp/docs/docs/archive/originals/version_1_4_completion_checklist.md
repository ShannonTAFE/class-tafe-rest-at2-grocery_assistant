# Version 1.4 Completion Checklist

## Version Summary

Version 1.4 completes the project transition from single-record workflows to safe batch meal workflows.

Version 1.4 contains three stages:

```text
Version 1.4A — Core service refactor
Version 1.4B — Intake-only batch meal logging
Version 1.4C — Inventory-linked batch meal logging
```

The version is complete when the codebase supports both safe batch logging paths:

```text
add_meal_with_items
    Creates one parent meal and multiple child intake items.
    Does not deduct inventory.

add_meal_with_inventory_items
    Creates one parent meal and multiple child intake items.
    Deducts explicitly selected inventory items.
    Creates linked inventory consumption records.
```

---

## Version 1.4A — Refactor Foundation

Status: Complete

Completed outcomes:

- Extracted schema constants into focused schema module.
- Extracted domain constants into constants module.
- Extracted shared service utilities.
- Extracted inventory rules.
- Extracted intake validation helpers.
- Extracted consumption helpers.
- Extracted waste helpers.
- Extracted relationship helpers.
- Extracted transaction-style related CSV save helper.
- Reduced pressure on `grocery_service.py` before adding batch workflows.

Design rule:

```text
Refactor structure without changing public behaviour.
```

---

## Version 1.4B — Intake-Only Batch Meal Logging

Status: Complete

Primary workflow:

```text
add_meal_with_items
```

Expected behaviour:

- Creates one parent intake history row.
- Creates one or more child intake item rows.
- Validates the parent meal before writing.
- Validates every child item before writing.
- Links every child item to the created `intake_id`.
- Saves related intake CSV updates together.
- Returns the created parent and child records.

Expected non-behaviour:

- Does not deduct inventory.
- Does not create inventory consumption records.
- Does not create food waste records.
- Does not auto-learn aliases.
- Does not create meal templates.
- Does not auto-roll up nutrition totals.

Completion checks:

```text
[ ] Service tests pass for add_meal_with_items.
[ ] MCP tool registration test includes add_meal_with_items.
[ ] MCP Inspector can call add_meal_with_items.
[ ] CSV check confirms intake history/items changed.
[ ] CSV check confirms inventory/consumption/waste unchanged.
```

---

## Version 1.4C — Inventory-Linked Batch Meal Logging

Status: Complete

Primary workflow:

```text
add_meal_with_inventory_items
```

Expected behaviour:

- Creates one parent intake history row.
- Creates child intake items for inventory-linked items.
- Creates child intake items for optional manual/untracked items.
- Deducts only explicitly supplied `inventory_items`.
- Copies inventory identity fields from the inventory row.
- Creates one linked inventory consumption record per inventory-linked child item.
- Links consumption records to both `intake_id` and `intake_item_id`.
- Saves intake history, intake items, inventory, and inventory consumption CSV updates together.
- Returns inventory update summaries.

Expected non-behaviour:

- Does not deduct inventory for manual items.
- Does not create food waste records.
- Does not auto-learn aliases.
- Does not create meal templates.
- Does not infer inventory deduction from meal names.
- Does not perform unit conversion.
- Does not auto-roll up nutrition totals.

Completion checks:

```text
[ ] Service tests pass for add_meal_with_inventory_items.
[ ] No-partial-write tests pass.
[ ] MCP tool registration test includes add_meal_with_inventory_items.
[ ] MCP Inspector can call add_meal_with_inventory_items.
[ ] CSV check confirms intake history/items changed.
[ ] CSV check confirms selected inventory rows changed.
[ ] CSV check confirms inventory consumption records were created.
[ ] CSV check confirms food waste unchanged.
```

---

## Final Version 1.4 Test Requirements

Run:

```powershell
pytest -q
```

Then reset to a freshly cleaned empty dataset and run the full curl workflow:

```powershell
python scripts/reset_empty_dataset_v1_4.py
python -m grocery_assistant_mcp.streamable_http_server
```

Use the curl requests in:

```text
docs/curl_requests/v1_4/
```

The final curl workflow should prove:

```text
1. The server initializes correctly.
2. Tools are visible.
3. Resources are visible/readable.
4. Inventory can be seeded from an empty dataset.
5. add_meal_with_items works as intake-only batch logging.
6. add_meal_with_inventory_items works as inventory-linked batch logging.
7. Inventory consumption records are linked to intake records.
8. Food waste remains unchanged.
```

---

## Version 1.4 Closeout Definition

Version 1.4 is closed when:

```text
[ ] Full pytest suite passes.
[ ] Fresh empty dataset reset succeeds.
[ ] Curl workflow succeeds end-to-end.
[ ] MCP Inspector manual workflow succeeds.
[ ] README and testing docs are updated.
[ ] Development journal records Version 1.4A/1.4B/1.4C.
[ ] Final docs commit is made.
```

Recommended final commit:

```powershell
git add docs/ scripts/
git commit -m "docs: close out Version 1.4"
```
