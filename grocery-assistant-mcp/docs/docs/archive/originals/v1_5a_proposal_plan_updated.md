# Version 1.5A Proposal Plan — Planning Signal Foundation

**Updated:** 2026-05-19  
**Status:** Approved planning direction  
**Implementation mode:** Planning and architecture only; no code in this document

---

## Purpose

Version 1.5A should become the planning-signal foundation for the Grocery Assistant MCP project.

The goal is not to build the full recommendation system yet. The goal is to create the reusable layer that allows future recommendation tools to reason from grocery data safely, consistently, and explainably.

The project has already moved through several important phases:

```text
Version 1.0  — read-only resources
Version 1.1  — safe write tools
Version 1.2  — intake and inventory linking foundations
Version 1.3  — inventory and stock-state improvements
Version 1.4  — controlled transaction-style meal and inventory workflows
Version 1.5  — planning intelligence and signal-based recommendations
Version 1.5A — planning signal foundation
```

The key Version 1.5A question is:

```text
How do we give the LLM agent the cleanest, safest, most useful planning signals possible before building recommendation tools?
```

---

## Accepted Direction

Version 1.5 should not begin with a machine-learning recommender or a complex meal suggestion engine.

Instead, Version 1.5 should begin with a structured signal layer.

The approved architecture direction is:

```text
raw grocery records
   ↓
interpreted planning signals
   ↓
agent reasoning
   ↓
recommendations / warnings / next actions
   ↓
future feedback collection
   ↓
future learning over time
```

Version 1.5A should therefore produce a read-only planning context tool that helps the agent understand:

```text
what is available
what is low
what is out
what is expired
what should be used soon
what data is missing
what assumptions are being made
what actions would require explicit confirmation
```

---

## Version 1.5 vs Version 1.5A

## Version 1.5 Overall Scope

Version 1.5 is the broader planning-intelligence phase.

It can eventually include:

```text
planning context review
low-stock review
use-soon review
restock suggestions
basic meal suggestions
recommendation event logging
feedback-aware ranking
preference-aware suggestions
```

## Version 1.5A Specific Scope

Version 1.5A should be narrower:

```text
Create the signal contract and planning response shape.
Prove that the planning layer can read data and produce useful signals.
Keep it read-only.
Do not mutate grocery records.
Do not build a final recommendation engine yet.
```

A strong Version 1.5A outcome is:

```text
The MCP server can return a structured planning context that an LLM agent can use to reason safely about current grocery data.
```

---

## Core Design Principle

The main rule for Version 1.5A is:

```text
Signals can guide suggestions, but suggestions are not actions.
```

The planning layer may say:

```text
Spinach should be prioritised because it is in stock and expires soon.
```

It should not automatically:

```text
log spinach as eaten
deduct spinach from inventory
create a shopping list item
save a preference
create a recommendation feedback record
```

Any state-changing operation should remain explicit and should go through existing write tools.

---

## Source Records vs Derived Signals

The existing CSV files should remain source-of-truth records.

They describe what happened or what currently exists.

Examples:

```text
user_inventory.csv
user_intake_history.csv
user_intake_items.csv
user_inventory_consumption.csv
user_waste.csv
```

These should not become overloaded machine-learning feature tables.

Instead, planning features should be derived by the planning layer.

```text
source records
   ↓
read services
   ↓
derived planning features
   ↓
planning signals
   ↓
agent response
```

This keeps the project cleaner and makes future recommendation logic easier to test.

---

## Proposed File Structure

A dedicated planning layer should be used instead of placing all planning logic inside `grocery_service.py`.

Recommended structure:

```text
grocery_assistant_mcp/
  core/
    planning_helpers.py
    planning_service.py
    planning_models.py        optional later

  mcp_tools/
    planning_tools.py

  tests/
    test_planning_helpers.py
    test_planning_service.py
    test_mcp_planning_tools.py
```

## Why Planning Should Be Separate

`grocery_service.py` is responsible for concrete grocery operations such as reading, validating, adding, updating, and linking records.

Planning is different.

It needs to:

```text
read multiple datasets
derive meaning from records
classify records into signals
attach confidence and data-quality metadata
warn about missing or uncertain data
suggest possible next actions
avoid mutation
```

Keeping planning separate protects the original service from becoming too large and mixed-purpose.

---

## Internal Architecture

Recommended architecture:

```text
CSV files
   ↓
existing grocery_service read functions
   ↓
planning_helpers.py
   ↓
planning_service.py
   ↓
mcp_tools/planning_tools.py
   ↓
LLM agent
```

## Layer 1 — Existing Read Functions

The planning layer should reuse existing read functions wherever possible.

Examples:

```text
list inventory records
search inventory records
review recent intake
summarise daily intake
list waste records if available
list consumption records if available
```

The planning layer should not duplicate CSV loading unless a genuine need appears.

## Layer 2 — Planning Helpers

`planning_helpers.py` should contain small interpretation helpers.

Examples:

```text
normalise stock status
identify low stock
identify very low stock
identify out-of-stock records
identify expired records
calculate days until expiry
identify use-soon items
classify missing quantity or unit values
build signal objects
build warnings
build safety metadata
```

These helpers are small, easy to test, and reusable across future planning tools.

## Layer 3 — Planning Service

`planning_service.py` should contain the user-facing planning functions.

Initial Version 1.5A responsibilities:

```text
build inventory planning signals
build basic recent-intake planning signals
build data-quality warnings
build standard planning response
build safety metadata
return read-only planning context
```

Future Version 1.5 responsibilities:

```text
review low-stock items
review use-soon items
suggest restock candidates
suggest meals from inventory
rank meal candidates
record recommendation events
record recommendation feedback
```

## Layer 4 — MCP Tool Wrapper

`mcp_tools/planning_tools.py` should expose the planning service to the MCP client.

The MCP wrapper should stay thin.

It should:

```text
receive simple tool arguments
call the planning service
return JSON-ready planning output
avoid embedding planning logic inside the wrapper
```

---

## Main Version 1.5A Tool

The main proposed tool is:

```text
review_planning_context
```

This tool should be read-only.

It should return:

```text
planning summary
inventory signals
recent-intake signals
data-quality warnings
safety metadata
suggested next actions
clear statement that no records were changed
```

Example user-facing intent:

```text
Review my grocery planning context.
What should the assistant know before making suggestions?
```

The tool should not yet try to produce a final meal recommendation.

---

## Planning Signal Contract

A planning signal should be a structured object that explains why something matters.

Recommended conceptual fields:

```text
signal_id
domain
signal_type
subject
severity
polarity
confidence
reason
evidence
data_quality
agent_guidance
limitations
```

## Field Meaning

| Field | Purpose |
|---|---|
| `signal_id` | Allows recommendations to reference the signal later. |
| `domain` | Identifies the source area, such as inventory, intake, data_quality, or system. |
| `signal_type` | Describes what kind of signal it is, such as use_soon or low_stock. |
| `subject` | Identifies the item, meal, record, or concept the signal refers to. |
| `severity` | Indicates urgency or importance. |
| `polarity` | Indicates whether the signal is positive, negative, neutral, or cautionary. |
| `confidence` | Indicates how much the system should trust the signal. |
| `reason` | Human-readable explanation. |
| `evidence` | Source fields or records that support the signal. |
| `data_quality` | Missing fields, assumptions, and completeness information. |
| `agent_guidance` | Guidance for how the LLM should use the signal. |
| `limitations` | What the signal should not be used for. |

---

## Foundation Signals for Version 1.5A

Version 1.5A should implement a small and stable signal set.

Recommended include list:

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
stock_id_available
write_requires_confirmation
recommendations_are_not_actions
```

These signals are valuable because they can be derived from existing records and do not require complex historical learning.

---

## Signals to Defer

These are good future ideas but should not be implemented in Version 1.5A:

```text
possible_staple
fast_consumption
slow_consumption
waste_risk
complete_meal_possible
partial_meal_possible
substitution_available
protein_opportunity
goal_alignment
cost_opportunity
convenience_opportunity
preference_fit
accepted_meal_pattern
rejected_ingredient
```

Reason for deferral:

```text
These require more historical data, more stable recommendation events, or more complex interpretation logic.
```

---

## Planning Response Schema

Every planning response should follow a consistent structure.

Recommended conceptual shape:

```text
status
planning_scope
generated_at
summary
signals
warnings
next_actions
safety
metadata
```

## Summary Block

The summary should provide a short overview for the agent.

Example summary concepts:

```text
number of inventory records reviewed
number of available items
number of low-stock items
number of expired items
number of use-soon items
number of recent intake records reviewed
main planning opportunity
main caution
```

## Signals Block

Signals should be grouped by domain:

```text
inventory
intake
data_quality
system
```

## Warnings Block

Warnings should highlight issues that may affect recommendation quality.

Examples:

```text
missing expiry dates
missing units
unknown stock status
low-confidence intake estimates
empty recent intake records
```

## Next Actions Block

Next actions should guide the agent without mutating data.

Examples:

```text
Ask user whether they want meal suggestions.
Ask user whether expired items should be removed.
Suggest reviewing low-stock items.
Suggest checking use-soon items.
Use write tools only after explicit confirmation.
```

## Safety Block

The safety block should be mandatory.

Recommended fields:

```text
read_only
records_changed
write_tools_called
requires_confirmation_before_write
safe_for_agent_suggestion
not_safe_for_automatic_mutation
```

Expected Version 1.5A values:

```text
read_only: true
records_changed: false
write_tools_called: false
requires_confirmation_before_write: true
safe_for_agent_suggestion: true
not_safe_for_automatic_mutation: true
```

---

## Data-Quality and Leniency Design

Version 1.5A should explicitly support imperfect user data.

The system should not fail simply because a record is incomplete.

Instead, it should describe the quality of the signal.

Examples:

```text
A food item with no expiry date can still be available inventory.
A food item with no unit can still be useful for a soft suggestion.
A meal with low nutrition confidence can still count as recently eaten.
An item with missing quantity should not be used for precise serving calculations.
```

This creates a leniency concept:

```text
complete enough for soft planning
not complete enough for precise calculation
not complete enough for automatic write action
```

Version 1.5A should start using this concept in warnings and confidence fields.

---

## Recommendation Boundary

Version 1.5A may return planning guidance, but it should not become a recommendation engine.

Allowed:

```text
This item is a use-soon candidate.
This item is low stock.
This record has missing quantity data.
The agent may ask whether the user wants meal suggestions.
```

Not yet allowed:

```text
Here is the final best meal.
Here is an automatically ranked meal plan.
I have created a shopping list.
I have deducted inventory.
I have saved your preference.
```

This keeps Version 1.5A focused and safe.

---

## Test Strategy

Version 1.5A should be heavily testable because it introduces interpretive logic.

## Test Group 1 — Signal Helper Tests

Test examples:

```text
in_stock item returns available_inventory
low item returns low_stock
very_low item returns very_low_stock
out item returns out_of_stock
expired item returns expired
future expiry inside threshold returns use_soon
blank expiry returns no_expiry_data
missing unit returns missing_unit
missing quantity returns missing_quantity
```

## Test Group 2 — Response Shape Tests

Ensure the planning response always includes:

```text
status
summary
signals
warnings
next_actions
safety
metadata
```

## Test Group 3 — No-Mutation Tests

These are critical.

Tests should confirm:

```text
review_planning_context does not change inventory CSV
review_planning_context does not change intake CSV
review_planning_context does not change consumption CSV
review_planning_context does not change waste CSV
records_changed is false
write_tools_called is false
```

## Test Group 4 — Agent Usefulness Tests

Test that outputs contain enough context for an LLM agent.

Expected planning output should include:

```text
human-readable reasons
source evidence
confidence
warnings
safe next actions
confirmation reminders
```

---

## Recommended Version 1.5A Deliverables

Version 1.5A should deliver:

```text
planning signal schema
standard planning response schema
safety metadata block
data-quality metadata block
inventory signal extraction
basic recent-intake signal extraction
warning generation
read-only review_planning_context tool
tests proving no mutation
documentation explaining the signal philosophy
```

---

## Version 1.5 Roadmap After 1.5A

Recommended staged path:

```text
Version 1.5A — Planning signal foundation
Version 1.5B — Low-stock, use-soon, and restock review tools
Version 1.5C — Basic meal suggestion from inventory
Version 1.5D — Recommendation event and feedback logging
Version 1.5E — Preference-aware and feedback-aware ranking
```

This roadmap avoids overbuilding and allows the project to collect better data before attempting machine learning.

---

## Version 1.5A Non-Goals

Do not include these in Version 1.5A:

```text
full meal recommendation ranking
shopping list generator
nutrition optimization engine
goal-based diet planning
automatic preference learning
machine-learning training pipeline
persistent signal-history dataset
recommendation feedback storage
automatic inventory mutation
```

These remain valuable future directions, but they depend on a clean signal foundation first.

---

## Final Definition

Version 1.5A can be defined as:

```text
Version 1.5A — Planning Signal Foundation

Goal:
Create a read-only planning layer that converts grocery records into structured signals for an LLM agent.

Main output:
review_planning_context

Core capabilities:
- classify inventory records into planning signals
- identify low-stock, out-of-stock, expired, and use-soon items
- identify recent intake context
- return data-quality warnings
- return source evidence for each signal
- return safety metadata confirming no records were changed
- prepare the architecture for future recommendations and feedback learning

Non-goals:
- no final recommendation ranking
- no machine-learning pipeline
- no automatic preference learning
- no write actions
- no shopping list mutation
```

---

## Recommendation

Proceed with Version 1.5A as a read-only planning signal foundation.

The strongest implementation target is:

```text
A stable review_planning_context tool that returns structured planning signals, warnings, confidence, evidence, and safety metadata.
```

This gives future recommendation tools a clean base to build from.
