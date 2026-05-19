# Version 1.5A — Planning Signal Foundation Implementation Notes

**Status:** Implemented and contract-tested  
**Checkpoint:** `review_planning_context` exposed through MCP Inspector and passing tests  
**Date:** 2026-05-19

---

## Purpose

Version 1.5A introduces the first planning-intelligence layer for the Grocery Assistant MCP project.

The goal of this stage is not to build a meal recommender, shopping-list generator, or machine-learning system. The goal is to create a safe, read-only signal foundation that an LLM agent can use before making future suggestions.

The central idea is:

```text
raw grocery records
   ↓
derived planning signals
   ↓
agent reasoning
   ↓
future recommendations
   ↓
future feedback collection
```

Version 1.5A focuses only on the first two layers.

---

## Main Deliverable

The main deliverable is the MCP-facing tool:

```text
review_planning_context
```

This tool reviews existing grocery data and returns structured planning context.

It is designed to answer:

```text
What should the assistant know about the user's grocery context before suggesting anything?
```

---

## Current Architecture

The Version 1.5A planning layer is separated from the existing grocery service logic.

Recommended structure:

```text
grocery_assistant_mcp/
  core/
    planning_helpers.py
    planning_service.py

  mcp_tools/
    planning_tools.py

tests/
  test_planning_helpers.py
  test_planning_service.py
  test_planning_context_contract.py
```

### Layer Responsibilities

```text
planning_helpers.py
```

Contains small, reusable helper functions for interpreting records and building planning signals.

```text
planning_service.py
```

Builds the full planning response by reading source records, generating signals, adding warnings, and returning safety metadata.

```text
planning_tools.py
```

Thin MCP wrapper that exposes the planning service to MCP clients.

The MCP wrapper should not contain heavy planning logic.

---

## Source Records vs Derived Signals

Existing CSV files remain the source of truth.

Examples:

```text
user_inventory.csv
user_intake_history.csv
user_intake_items.csv
user_inventory_consumption.csv
user_waste.csv
```

Version 1.5A does not turn these CSVs into machine-learning feature tables.

Instead, the planning layer reads these records and derives temporary planning signals from them.

This keeps the architecture cleaner:

```text
source CSV records
   ↓
read/list service functions
   ↓
planning signal generation
   ↓
structured MCP response
```

---

## Planning Signal Contract

A planning signal is a structured object that explains why a piece of grocery data matters.

The accepted Version 1.5A signal shape includes fields such as:

```text
signal_id
domain
signal_type
subject
severity
confidence
reason
evidence
data_quality
agent_guidance
```

### Field Meanings

| Field | Purpose |
|---|---|
| `signal_id` | Stable identifier for the generated signal. |
| `domain` | Source area such as inventory, intake, data_quality, or system. |
| `signal_type` | The kind of signal, such as available_inventory or low_stock. |
| `subject` | The item, meal, record, or concept the signal refers to. |
| `severity` | Urgency or importance of the signal. |
| `confidence` | How reliable the signal appears to be. |
| `reason` | Human-readable explanation. |
| `evidence` | Source fields or record identifiers supporting the signal. |
| `data_quality` | Missing fields, assumptions, or completeness notes. |
| `agent_guidance` | How an LLM agent should use the signal. |

---

## Foundation Signals in Version 1.5A

Version 1.5A supports a small, safe signal set.

Examples include:

```text
available_inventory
low_stock
very_low_stock
out_of_stock
expired
use_soon
no_expiry_data
missing_stock_status
missing_quantity
missing_unit
recently_eaten
no_recent_intake_records
write_requires_confirmation
recommendations_are_not_actions
```

A single source record may generate multiple signals.

For example, an item can be both:

```text
available_inventory
low_stock
```

This means the item can still be used in planning, but should also be treated as a restock or caution signal.

---

## Planning Response Contract

The planning response should remain structured and predictable.

Expected high-level response sections include:

```text
status
planning_scope
summary
signals
warnings
recommendations
next_actions
safety
metadata
```

### Important Version 1.5A Boundary

In Version 1.5A:

```text
recommendations should remain empty
```

This is intentional.

Version 1.5A prepares context for future recommendations but does not generate final recommendations yet.

---

## Safety Contract

The safety block is mandatory.

The accepted safety boundary is:

```text
read_only: true
inventory_mutation_performed: false
intake_mutation_performed: false
consumption_mutation_performed: false
waste_mutation_performed: false
shopping_list_mutation_performed: false
requires_user_confirmation_before_write: true
```

The planning context tool must not:

```text
modify inventory
modify intake records
modify consumption records
modify waste records
create shopping-list entries
deduct inventory
save user preferences
record recommendation feedback
```

Any write operation must happen through an explicit write tool after user confirmation.

---

## Next Actions Are Not Recommendations

The `next_actions` block is allowed in Version 1.5A, but it must be interpreted carefully.

Allowed purpose:

```text
safe routing hints for the agent
```

Examples:

```text
review_low_stock
log_with_inventory_items
update_inventory
```

These are not user-facing recommendations. They are suggestions about possible follow-up tool paths.

The system should not treat them as permission to mutate data.

---

## Test Coverage

Version 1.5A is protected by service, helper, and contract tests.

Recommended test groups:

```text
tests/test_planning_helpers.py
tests/test_planning_service.py
tests/test_planning_context_contract.py
```

### Contract Tests

The contract tests protect the response shape and Version 1.5A scope.

They check that:

```text
review_planning_context returns the expected top-level sections
signals contain required fields
safety.read_only is true
mutation flags are false
records_checked metadata is present
recommendations remain empty
next_actions remain routing hints
mutation-capable next actions require confirmation
```

The most important scope-protection rule is:

```text
Version 1.5A must not become the meal recommendation engine.
```

---

## Manual MCP Inspector Verification

MCP Inspector verification has confirmed:

```text
review_planning_context is visible as an MCP tool
review_planning_context can be called successfully
the response structure is accurate
the response contains safety metadata
tests pass after MCP verification
```

---

## Testing Commands

Run the focused contract tests:

```powershell
pytest tests/test_planning_context_contract.py -v
```

Run the planning tests:

```powershell
pytest tests/test_planning_helpers.py tests/test_planning_service.py tests/test_planning_context_contract.py -v
```

Run the full test suite:

```powershell
pytest
```

---

## Definition of Done for Version 1.5A

Version 1.5A can be considered complete when:

```text
review_planning_context is implemented
review_planning_context is registered as an MCP tool
MCP Inspector can see and call the tool
the response includes planning signals
the response includes safety metadata
the response includes records_checked metadata
recommendations remain empty
the tool is read-only
all tests pass
documentation explains the signal philosophy and safety boundary
```

At the current checkpoint, the implementation has passed the key technical checks.

---

## Non-Goals for Version 1.5A

Do not include these in Version 1.5A:

```text
meal recommendation ranking
shopping list generation
automatic inventory mutation
automatic preference learning
recommendation feedback logging
machine-learning training pipeline
nutrition optimization
goal-based diet planning
persistent signal-history dataset
```

These belong to later Version 1.5 stages.

---

## Recommended Next Stage

The next stage should be Version 1.5B.

Recommended focus:

```text
Version 1.5B — focused inventory planning review tools
```

Possible future tools:

```text
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
```

These should reuse the same planning signal helpers instead of creating separate interpretation logic.

Version 1.5B should still be careful not to jump too quickly into full meal recommendation logic.

---

## Development Notes

The most important design decision from Version 1.5A is:

```text
Signals can guide suggestions, but suggestions are not actions.
```

This keeps the assistant useful while preventing accidental writes or premature automation.

The project now has a clean foundation for gradually moving from:

```text
record keeping
   ↓
planning signals
   ↓
safe reviews
   ↓
basic suggestions
   ↓
feedback-aware recommendations
   ↓
future learning over time
```
