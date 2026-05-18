# Version 1.5A Proposal Plan — Planning Architecture Foundation

## Purpose

Version 1.5A should be treated as the planning intelligence foundation, not as the first individual feature.

The goal is to build the layer that makes every later planning tool useful to the agent.

The project has already moved from read-only resources, to safe writes, to controlled consumption, to transaction-like meal workflows, and now into planning intelligence and suggestion workflows.

The safety boundary remains clear:

```text
Suggestions can be intelligent, but writes should remain explicit.
```

Version 1.5A should answer this:

```text
How do we give the LLM agent the cleanest, safest, most useful planning signals possible?
```

---

# Version 1.5A — Planning Architecture Foundation

## Core Purpose

Version 1.5A should create the reusable planning layer that future tools depend on.

It should not yet try to solve every planning problem.

Instead, it should define:

```text
1. Where planning logic lives
2. What planning tool responses look like
3. What safety metadata every planning result includes
4. How planning functions read existing grocery records
5. How planning functions avoid mutation
6. How the agent can understand confidence, warnings, and next actions
7. How tests prove that suggestions are read-only
```

This matters because Version 1.5 is the first time the server starts returning interpretive outputs, not just factual records or controlled writes.

---

# Main Design Principle

For best agent results, Version 1.5A should make every planning output:

```text
structured
explainable
safe
ranked
grounded
testable
agent-friendly
```

The agent should not receive vague blobs like:

```json
{
  "suggestion": "Maybe make chicken rice."
}
```

It should receive structured reasoning like:

```json
{
  "recommendation_type": "meal_suggestion",
  "title": "Chicken rice bowl",
  "priority": "high",
  "confidence": "medium",
  "reason": "Uses available chicken and rice while avoiding expired yoghurt.",
  "supporting_signals": [
    "Chicken breast is in stock.",
    "Rice is available in pantry.",
    "Yoghurt is expired and excluded."
  ],
  "warnings": [],
  "requires_user_confirmation_before_write": true,
  "suggested_follow_up_tools": [
    "add_meal_with_inventory_items"
  ]
}
```

That gives the agent everything it needs to produce a good user-facing response.

---

# Proposed File Structure

A dedicated planning layer is recommended instead of mixing this into `grocery_service.py`.

```text
grocery_assistant_mcp/
  core/
    planning_service.py
    planning_helpers.py
    planning_models.py        optional
  mcp_tools/
    planning_tools.py
  tests/
    test_planning_helpers.py
    test_planning_service.py
    test_mcp_planning_tools.py
```

## Why Separate Planning Files?

`grocery_service.py` already owns concrete inventory, intake, waste, and consumption operations.

Planning is different.

It is not just:

```text
read row
validate input
write row
```

It is:

```text
read multiple datasets
derive signals
rank possible recommendations
explain reasoning
warn about uncertainty
avoid mutation
suggest safe next actions
```

Keeping it separate will make the architecture cleaner.

---

# Recommended Internal Architecture

Use this layered structure:

```text
CSV data
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

Reuse existing safe read functions wherever possible.

Examples:

```python
list_inventory_items()
search_inventory()
review_recent_intake()
summarise_daily_intake()
```

The planning layer should not duplicate CSV loading logic unless needed.

---

## Layer 2 — `planning_helpers.py`

This file should contain small reusable interpretation helpers.

Examples:

```python
normalize_stock_status()
is_attention_stock_status()
is_out_of_stock()
is_low_stock()
is_expired()
is_use_soon()
safe_parse_date()
days_until_expiry()
classify_inventory_item_for_planning()
rank_priority()
build_safety_metadata()
```

These helpers make future planning tools consistent.

---

## Layer 3 — `planning_service.py`

This file should contain the user-facing planning functions.

Initial 1.5A functions can be minimal:

```python
build_planning_context()
build_inventory_planning_signals()
build_intake_planning_signals()
build_standard_planning_response()
```

Later Version 1.5 stages can add:

```python
review_low_stock_items()
suggest_restock_items()
review_recent_intake_patterns()
suggest_meals_from_inventory()
suggest_next_meal()
draft_shopping_list()
review_food_waste_patterns()
```

---

## Layer 4 — `mcp_tools/planning_tools.py`

This should only wrap service functions.

This keeps the existing design principle intact:

```text
MCP wrappers stay thin.
Business logic stays in the service layer.
```

---

# Best Possible Planning Response Schema

This is the most important part of Version 1.5A.

A standard response structure should be followed by every planning function.

```python
{
    "tool_name": "suggest_meals_from_inventory",
    "summary": "3 meal suggestions found using available inventory.",
    "result_type": "planning_suggestion",
    "status": "success",

    "inputs": {
        "meal_type": "dinner",
        "max_suggestions": 3
    },

    "signals": {
        "inventory_signals": [],
        "intake_signals": [],
        "waste_signals": [],
        "consumption_signals": []
    },

    "recommendations": [],

    "warnings": [],

    "next_actions": [],

    "safety": {
        "read_only": True,
        "inventory_mutation_performed": False,
        "intake_mutation_performed": False,
        "consumption_mutation_performed": False,
        "waste_mutation_performed": False,
        "shopping_list_mutation_performed": False,
        "requires_user_confirmation_before_write": True
    },

    "metadata": {
        "records_checked": {
            "inventory": 0,
            "intake_history": 0,
            "intake_items": 0,
            "consumption": 0,
            "waste": 0
        },
        "generated_at": "2026-05-18",
        "version": "1.5A"
    }
}
```

This is verbose, but useful for MCP planning tools.

The agent can ignore what it does not need, but the structure gives it clear context.

---

# Essential Design Idea: Signals Before Recommendations

For best agent results, avoid jumping straight from raw data to suggestions.

Use this internal pattern:

```text
Raw records
   ↓
Signals
   ↓
Recommendations
   ↓
Next actions
```

## Example

Raw inventory item:

```json
{
  "food_item": "Eggs",
  "quantity": 1,
  "stock_status": "very_low",
  "expiry_date": "2026-05-20"
}
```

Planning signal:

```json
{
  "signal_type": "inventory_attention",
  "food_item": "Eggs",
  "severity": "high",
  "reason": "Item is very_low and expires soon.",
  "source_fields": ["stock_status", "expiry_date"]
}
```

Recommendation:

```json
{
  "recommendation_type": "restock",
  "food_item": "Eggs",
  "priority": "high",
  "reason": "Eggs are very low and expire soon.",
  "suggested_action": "Consider adding eggs to a shopping list draft."
}
```

This gives the agent much better reasoning material.

---

# Proposed Shared Data Concepts

## 1. Planning Signal

A planning signal is a small interpreted fact.

Example:

```python
{
    "signal_type": "low_stock",
    "severity": "medium",
    "food_item": "Milk",
    "stock_id": "inv_004",
    "reason": "Stock status is low.",
    "source": "inventory",
    "source_fields": ["stock_status"]
}
```

Recommended signal types:

```text
available_inventory
low_stock
very_low_stock
out_of_stock
expired
use_soon
recently_eaten
repeated_meal
missing_nutrition_estimates
possible_staple
possible_waste_pattern
optional_missing_ingredient
```

---

## 2. Recommendation

A recommendation is what the agent can present or use.

Example:

```python
{
    "recommendation_type": "meal",
    "title": "Chicken rice bowl",
    "priority": "high",
    "confidence": "medium",
    "reason": "Uses available chicken and rice.",
    "supporting_signals": ["available_inventory", "avoid_recent_repetition"],
    "warnings": [],
    "suggested_follow_up_tools": ["add_meal_with_inventory_items"]
}
```

Recommended recommendation types:

```text
meal_suggestion
next_meal
restock
shopping_list_draft_item
intake_pattern_observation
waste_pattern_observation
```

---

## 3. Warning

Warnings tell the agent what not to overclaim.

Example:

```python
{
    "warning_type": "low_confidence",
    "message": "Nutrition estimates are missing for several recent meals.",
    "agent_guidance": "Avoid making strong nutrition claims."
}
```

Recommended warning types:

```text
expired_items_excluded
missing_inventory_data
missing_intake_data
low_confidence
ambiguous_stock_status
no_recent_intake_records
no_available_inventory
write_requires_confirmation
```

---

## 4. Next Action

Next actions help the agent route follow-up user intent.

Example:

```python
{
    "label": "Log this meal with inventory deduction",
    "tool_name": "add_meal_with_inventory_items",
    "requires_confirmation": True,
    "reason": "This would create intake rows and deduct inventory."
}
```

Recommended next action types:

```text
read_more
ask_user_to_confirm
log_intake_only
log_with_inventory_items
draft_shopping_list
update_inventory
review_low_stock
```

This is important for MCP agent performance because it helps the agent know which tool to use next.

---

# Safety Metadata Should Be Mandatory

Every planning function should return this safety block.

```python
"safety": {
    "read_only": True,
    "inventory_mutation_performed": False,
    "intake_mutation_performed": False,
    "consumption_mutation_performed": False,
    "waste_mutation_performed": False,
    "shopping_list_mutation_performed": False,
    "requires_user_confirmation_before_write": True
}
```

This is valuable for the agent because it can see:

```text
This was only a suggestion.
No records were changed.
A write needs confirmation.
```

That reinforces the project’s safety boundary.

---

# What Version 1.5A Should Create Immediately

Version 1.5A should not yet implement all final tools.

It should implement the foundation and maybe one simple planning context function.

## Create `planning_helpers.py`

Suggested functions:

```python
ATTENTION_STOCK_STATUSES = {"low", "very_low", "out", "expired"}

USABLE_STOCK_STATUSES = {"in_stock", "low", "very_low"}

NON_USABLE_STOCK_STATUSES = {"out", "expired"}

def normalize_text(value: object) -> str:
    ...

def normalize_stock_status(value: object) -> str:
    ...

def is_low_stock_status(stock_status: str) -> bool:
    ...

def is_out_of_stock_status(stock_status: str) -> bool:
    ...

def is_expired_status(stock_status: str) -> bool:
    ...

def safe_parse_date(value: object) -> date | None:
    ...

def days_until(target_date: date, today: date | None = None) -> int | None:
    ...

def classify_expiry(expiry_date: str, today: date | None = None, use_soon_days: int = 7) -> str:
    ...

def build_safety_metadata(requires_confirmation: bool = True) -> dict:
    ...
```

---

## Create `planning_service.py`

Initial functions:

```python
def build_planning_context(
    include_inventory: bool = True,
    include_recent_intake: bool = True,
    include_consumption: bool = False,
    include_waste: bool = False,
    recent_days: int = 7,
) -> dict:
    ...
```

This would return a clean context object for future tools.

Example:

```python
{
    "summary": "Planning context created.",
    "inventory": {
        "records_checked": 12,
        "available_items": [...],
        "attention_items": [...],
        "expired_items": [...],
        "use_soon_items": [...]
    },
    "recent_intake": {
        "records_checked": 8,
        "recent_meals": [...],
        "recent_meal_names": [...]
    },
    "warnings": [],
    "safety": {
        "read_only": True,
        "inventory_mutation_performed": False,
        "intake_mutation_performed": False,
        "requires_user_confirmation_before_write": True
    }
}
```

This function becomes the foundation for later 1.5 tools.

---

## Create `build_standard_planning_response()`

This helper prevents inconsistent response shapes.

```python
def build_standard_planning_response(
    tool_name: str,
    summary: str,
    recommendations: list[dict] | None = None,
    signals: dict | None = None,
    warnings: list[dict] | None = None,
    next_actions: list[dict] | None = None,
    inputs: dict | None = None,
    metadata: dict | None = None,
) -> dict:
    ...
```

It should always inject:

```python
"safety": build_safety_metadata()
```

That way every planning tool automatically declares itself read-only.

---

# Best Possible Design Choices for the Agent

## 1. Return Reasons, Not Just Results

Bad:

```json
{
  "food_item": "Eggs",
  "priority": "high"
}
```

Better:

```json
{
  "food_item": "Eggs",
  "priority": "high",
  "reason": "Marked very_low and useful across common meals.",
  "source_signals": ["very_low_stock", "possible_staple"]
}
```

The agent needs the reason to explain the result.

---

## 2. Return Confidence

Use simple values:

```text
high
medium
low
```

Do not over-engineer numeric confidence yet.

Example:

```json
{
  "confidence": "medium",
  "confidence_reason": "Inventory records are available, but recent intake data is sparse."
}
```

This helps the agent avoid sounding too certain.

---

## 3. Return Warnings for Missing Data

Example:

```json
{
  "warning_type": "missing_recent_intake",
  "message": "No recent intake records were found.",
  "agent_guidance": "Do not claim the suggestion avoids recent repetition."
}
```

This prevents hallucinated reasoning.

---

## 4. Return Source Fields

Example:

```json
{
  "source_fields": ["stock_status", "expiry_date", "category"]
}
```

This makes outputs more auditable and easier to debug.

---

## 5. Return Follow-Up Tool Hints

Example:

```json
{
  "suggested_follow_up_tools": [
    {
      "tool_name": "add_meal_with_inventory_items",
      "when_to_use": "Only if the user explicitly wants to log this meal and deduct linked inventory."
    },
    {
      "tool_name": "add_meal_with_items",
      "when_to_use": "Use for intake-only logging without inventory deduction."
    }
  ]
}
```

This is one of the best ways to help the agent choose the right next tool.

---

# Version 1.5A Test Strategy

The tests should prove that the planning layer is safe, stable, and agent-friendly.

## Test Group 1 — Helper Tests

```python
def test_normalize_stock_status_handles_blank():
    ...

def test_is_low_stock_status_detects_low_and_very_low():
    ...

def test_classify_expiry_returns_expired():
    ...

def test_classify_expiry_returns_use_soon():
    ...

def test_build_safety_metadata_is_read_only():
    ...
```

---

## Test Group 2 — Response Shape Tests

```python
def test_standard_planning_response_has_required_keys():
    ...

def test_standard_planning_response_includes_safety_block():
    ...

def test_standard_planning_response_defaults_lists_to_empty_lists():
    ...

def test_standard_planning_response_preserves_inputs():
    ...
```

---

## Test Group 3 — No-Mutation Tests

This is critical.

```python
def test_build_planning_context_does_not_mutate_inventory_csv():
    before = USER_INVENTORY_CSV.read_text()

    result = build_planning_context(include_inventory=True)

    after = USER_INVENTORY_CSV.read_text()
    assert before == after
    assert result["safety"]["inventory_mutation_performed"] is False
```

Do the same later for intake, consumption, and waste.

---

## Test Group 4 — Agent Usefulness Tests

These tests make sure the tool output is not just technically correct, but useful for agent reasoning.

```python
def test_planning_context_returns_agent_warnings_for_missing_intake():
    ...

def test_planning_context_returns_source_fields_for_inventory_signals():
    ...

def test_planning_context_returns_next_actions_when_write_would_be_needed():
    ...
```

---

# Recommended Version 1.5A Scope

## Include in Version 1.5A

```text
planning_helpers.py
planning_service.py
standard planning response schema
safety metadata helper
planning context builder
inventory classification helpers
expiry classification helpers
basic recent intake context helper
tests for response shape
tests for safety metadata
tests for no mutation
documentation update
```

## Exclude from Version 1.5A

```text
final low-stock review tool
final restock suggestion tool
final meal suggestion tool
final shopping list draft tool
final food waste pattern review
complex scoring system
recipe logic
nutrition recommendation logic
automatic learning
persistent shopping list files
```

Why exclude these?

Because Version 1.5A is the foundation. We do not want to muddy it with feature-specific logic too early.

---

# Proposed Version 1.5A Implementation Plan

## Step 1 — Create Planning Helper Constants

```python
ATTENTION_STOCK_STATUSES = {"low", "very_low", "out", "expired"}
USABLE_STOCK_STATUSES = {"in_stock", "low", "very_low"}
NON_USABLE_STOCK_STATUSES = {"out", "expired"}
UNKNOWN_STOCK_STATUS = "unknown"
```

---

## Step 2 — Create Status and Date Helpers

```python
normalize_stock_status()
is_attention_stock_status()
is_usable_stock_status()
safe_parse_date()
classify_expiry()
```

---

## Step 3 — Create Safety Metadata Helper

```python
build_safety_metadata()
```

Expected output:

```python
{
    "read_only": True,
    "inventory_mutation_performed": False,
    "intake_mutation_performed": False,
    "consumption_mutation_performed": False,
    "waste_mutation_performed": False,
    "shopping_list_mutation_performed": False,
    "requires_user_confirmation_before_write": True
}
```

---

## Step 4 — Create Standard Planning Response Builder

```python
build_standard_planning_response()
```

This should guarantee consistent output for every future planning tool.

---

## Step 5 — Create Initial Planning Context Builder

```python
build_planning_context()
```

This should gather and classify inventory and optionally recent intake.

It does not need to be perfect yet.

Its job is to prove the architecture.

---

## Step 6 — Add Tests

Start with helper tests, then response shape, then no-mutation.

---

## Step 7 — Add a Minimal MCP Wrapper Only If Useful

You could expose:

```text
build_planning_context
```

as an internal/debug planning tool, but user-facing MCP tools should be meaningful.

A better option:

```text
review_planning_context
```

Tool description:

```text
Build a read-only planning context from inventory and recent intake records.
This tool prepares structured signals for planning, but does not mutate records.
```

This can be a useful diagnostic MCP tool for Version 1.5A.

---

# Proposed MCP Tool for Version 1.5A

## `review_planning_context`

Purpose:

```text
Return a read-only planning context that helps an agent understand inventory attention items, use-soon items, expired items, recent meals, warnings, and safe next actions.
```

Inputs:

```python
recent_days: int = 7
include_inventory: bool = True
include_recent_intake: bool = True
include_waste: bool = False
include_consumption: bool = False
```

Output:

```python
{
    "summary": "Planning context prepared from inventory and recent intake.",
    "signals": {
        "inventory_signals": [...],
        "intake_signals": []
    },
    "warnings": [],
    "next_actions": [],
    "safety": {
        "read_only": True,
        "inventory_mutation_performed": False,
        "intake_mutation_performed": False,
        "requires_user_confirmation_before_write": True
    }
}
```

This gives a practical MCP-facing Version 1.5A tool without prematurely building final recommendation tools.

---

# Best Version 1.5A Outcome

At the end of Version 1.5A, we should be able to say:

```text
We now have a read-only planning architecture that converts grocery records into structured planning signals for an agent.

The planning layer has a standard response format, safety metadata, warnings, source signals, and no-mutation tests.

Future Version 1.5 tools can build on this foundation without each inventing their own structure.
```

That is the right foundation for best possible agent results.

---

# Recommended Version 1.5A Deliverables

```text
1. core/planning_helpers.py
2. core/planning_service.py
3. mcp_tools/planning_tools.py
4. tests/test_planning_helpers.py
5. tests/test_planning_service.py
6. tests/test_mcp_planning_tools.py
7. documentation update:
   - Version 1.5A purpose
   - planning response schema
   - safety metadata
   - agent/MCP relationship
8. MCP Inspector request for review_planning_context
9. Curl request for review_planning_context
```

---

# Final Proposed Version 1.5A Definition

```text
Version 1.5A — Planning Architecture Foundation

Goal:
Create a read-only planning layer that converts grocery records into structured, explainable, testable signals for an LLM agent.

Primary tool:
review_planning_context

Core outputs:
- planning signals
- recommendations placeholder
- warnings
- next actions
- safety metadata
- records checked metadata

Safety rule:
1.5A must not mutate inventory, intake, consumption, waste, or shopping list records.

Success criteria:
The agent receives cleaner planning context than raw CSV records alone, while all mutations remain routed through existing explicit write tools.
```

## Recommendation

Build `review_planning_context` first, not `suggest_meals_from_inventory`.

This gives the project the reusable signal layer that every future Version 1.5 tool will depend on.
