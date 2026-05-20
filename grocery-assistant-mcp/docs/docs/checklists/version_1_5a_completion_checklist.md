# Version 1.5A Completion Checklist

Use this checklist before closing Version 1.5A or beginning Version 1.5B.

---

## Implementation

- [ ] `planning_helpers.py` exists.
- [ ] `planning_service.py` exists.
- [ ] `planning_tools.py` exists.
- [ ] `review_planning_context` is implemented.
- [ ] `review_planning_context` is registered inside the MCP tool registry.
- [ ] The MCP wrapper is thin and delegates planning logic to the service layer.

---

## MCP Verification

- [ ] Server starts successfully.
- [ ] MCP Inspector shows `review_planning_context`.
- [ ] MCP Inspector can call `review_planning_context`.
- [ ] The response contains planning signals.
- [ ] The response contains safety metadata.
- [ ] The response contains `records_checked` metadata.
- [ ] The response does not perform writes.

---

## Test Verification

- [ ] Planning helper tests pass.
- [ ] Planning service tests pass.
- [ ] Planning context contract tests pass.
- [ ] Full test suite passes.

Commands:

```powershell
pytest tests/test_planning_helpers.py tests/test_planning_service.py tests/test_planning_context_contract.py -v
pytest
```

---

## Contract Rules

- [ ] `recommendations` remains empty in Version 1.5A.
- [ ] Safety metadata confirms read-only behaviour.
- [ ] Mutation flags remain false.
- [ ] Next actions are routing hints only.
- [ ] Mutation-capable next actions require user confirmation.
- [ ] Signals include evidence.
- [ ] Signals include confidence or data-quality context.
- [ ] The tool does not deduct inventory.
- [ ] The tool does not create shopping list entries.
- [ ] The tool does not save user preferences.

---

## Documentation

- [ ] Version 1.5A implementation notes are documented.
- [ ] Signal contract is documented.
- [ ] Safety boundary is documented.
- [ ] Non-goals are documented.
- [ ] Version 1.5B next direction is documented.

---

## Commit

Recommended commit after all checks pass:

```powershell
git add .
git commit -m "Complete v1.5a planning signal foundation"
```

---

## Ready for Version 1.5B?

Only begin Version 1.5B after the above items are complete.

Recommended Version 1.5B focus:

```text
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
```
