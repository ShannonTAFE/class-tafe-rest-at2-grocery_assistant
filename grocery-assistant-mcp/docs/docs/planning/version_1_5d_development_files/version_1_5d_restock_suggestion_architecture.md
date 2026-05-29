# Version 1.5D — Restock Suggestion Architecture Investigation

## Status

Planning document for the next Version 1.5 stage.

Version 1.5A, 1.5B, and 1.5C have already created the foundation for a read-only planning and recommendation layer:

- `review_planning_context`
- `review_low_stock_items`
- `review_use_soon_items`
- `review_inventory_data_quality`
- `draft_meal_suggestions`

Version 1.5D should extend this direction with meal-aware restock drafts.

The recommended main deliverable is:

```text
draft_restock_suggestions
```

This should be a read-only planning tool. It should not create shopping-list rows, update inventory, log intake, deduct stock, or create waste records.

---

## Purpose

Version 1.5D should investigate and implement a safe restock reasoning layer.

The goal is not to simply say:

```text
rice is low → buy rice
```

The better goal is:

```text
rice is low
rice is a base ingredient
rice supports several meal opportunities
therefore rice is a stronger restock candidate than a low item that is not connected to current meals
```

This keeps the project moving from raw record access toward planning intelligence while preserving the major Version 1.5 safety boundary:

```text
Planning tools may suggest, draft, rank, explain, and warn.
Planning tools must not silently mutate user records.
```

---

## Current Code Review Summary

The uploaded files show a strong foundation for Version 1.5D.

### Existing strengths

#### 1. Stable planning response pattern

`planning_service.py` already has a standard planning response builder with:

- `tool_name`
- `summary`
- `result_type`
- `status`
- `inputs`
- `signals`
- `recommendations`
- `warnings`
- `next_actions`
- `safety`
- `metadata`

This is valuable because Version 1.5D should follow the same structure.

#### 2. Read-only safety metadata already exists

`planning_helpers.py` includes `build_safety_metadata`, which returns the correct read-only contract:

```text
read_only = True
inventory_mutation_performed = False
intake_mutation_performed = False
consumption_mutation_performed = False
waste_mutation_performed = False
shopping_list_mutation_performed = False
requires_user_confirmation_before_write = True
```

Version 1.5D should reuse this instead of creating a separate safety shape.

#### 3. Meal suggestions already produce structured gap hints

`meal_suggestion_helpers.py` already builds structured `gap_signals` instead of only returning prose.

This is important because `draft_restock_suggestions` should use structured evidence, not parse human-readable strings such as `restock_hint`.

Current meal suggestion outputs include useful fields such as:

```text
main_items_used
use_soon_items_used
low_items_used
missing_or_low_items
gap_hints
restock_hint
```

#### 4. MCP wrappers are thin

`planning_tools.py` and `meal_suggestion_tools.py` mostly delegate to service-layer functions. This should continue.

MCP wrappers should describe the tool and expose arguments. They should not contain ranking logic, business rules, or CSV write behaviour.

#### 5. Existing tests already define important safety expectations

The current tests verify behaviours such as:

- empty inventory returns a safe response
- use-soon items increase meal priority
- out-of-stock items are not used as main ingredients
- expired items are excluded from usable meal suggestions
- missing expiry data does not block suggestions
- focused planning reviews keep recommendations empty where appropriate
- focused review tools preserve read-only safety contracts

Version 1.5D should add tests in the same style.

---

## Current Design Gaps Relevant to 1.5D

The code is ready for 1.5D, but there are several areas to improve before or during implementation.

### Gap 1 — Meal gap signals do not carry enough meal context

Current `gap_signals` contain fields like:

```text
food_item
stock_id
gap_type
roles
message
```

For restock ranking, it would be useful to include:

```text
meal_name
template_id
template_name
gap_role
gap_strength
gap_source
candidate_kind
```

Without this, restock logic can still work by reading `suggestion["gap_hints"]` inside each suggestion, but the global `signals["gap_signals"]` list is less useful because it loses which meal each gap came from.

Recommended change:

```python
{
    "food_item": item["food_item"],
    "stock_id": item["stock_id"],
    "gap_type": gap_type,
    "roles": item["roles"],
    "matched_roles": matched_roles,
    "gap_role": "supporting" or "optional" or "main_low",
    "template_id": template["template_id"],
    "template_name": template["meal_name"],
    "message": _gap_message(item=item, gap_type=gap_type),
}
```

The actual `meal_name` may be built later after main items are selected, so it can be added either:

1. when building the match object, or
2. when transforming match gaps into restock candidate signals.

### Gap 2 — Some meal suggestion helper functions are private but now useful across features

Functions such as `_build_item_signals`, `_infer_roles`, `_match_template`, and `_build_gap_signals` are currently private to `meal_suggestion_helpers.py`.

That was fine for 1.5C.

For 1.5D, parts of this logic become shared planning infrastructure.

Recommended direction:

```text
Keep low-level pure helper behaviour reusable.
Avoid importing underscore/private helpers from restock modules where possible.
```

Possible refactor:

```text
core/meal_signal_helpers.py
  build_inventory_item_signals
  infer_food_roles
  build_meal_template_matches
  build_meal_gap_signals

core/meal_suggestion_helpers.py
  convert meal signals into final meal suggestion draft response

core/restock_helpers.py
  convert inventory and meal-gap signals into restock candidates
```

This would give Version 1.5 a cleaner signal foundation.

### Gap 3 — Meal suggestions do not currently use the standard planning response builder

`draft_meal_suggestions` currently returns a good response shape, but it does not include the same `safety` and `metadata` blocks used by `planning_service.py`.

This is not a blocker, but it would be better for consistency.

Recommended non-breaking improvement:

```text
Add safety metadata to draft_meal_suggestions.
Add metadata with generated_at, version, records_checked, and reference_date.
Keep existing fields unchanged so current tests and agent usage still work.
```

This would align 1.5C and 1.5D with the same planning contract.

### Gap 4 — Stock and expiry normalisation logic exists in more than one place

`planning_helpers.py` has `normalize_stock_status`, `safe_parse_date`, and `classify_expiry`.

`meal_suggestion_helpers.py` has `_normalise_status` and `_parse_date_or_status`.

This duplication is understandable during staged development, but it may drift over time.

Recommended direction:

```text
Use planning_helpers.py as the shared source for stock status and date interpretation.
```

This can be a small cleanup before or during 1.5D, but it does not need to become a large refactor.

### Gap 5 — Current meal matching only suggests meals already possible

The current meal suggestion architecture is deliberately conservative: it suggests meals when a required item is already available.

That is good for meal suggestions.

For restock suggestions, a future improvement may be:

```text
near-miss meal matching
```

Example:

```text
You have wraps, cheese, and vegetables, but no protein.
A protein option could unlock stronger wrap suggestions.
```

This is powerful but should probably not be part of the first 1.5D implementation unless time allows.

Recommended scope:

```text
1.5D-A:
  Use current possible meal suggestions and their gap hints.

1.5D-B or later:
  Add near-miss meal opportunities where one missing required role could unlock a meal.
```

---

## Recommended Version 1.5D Scope

### Include in 1.5D-A

```text
draft_restock_suggestions

restock candidates from:
  - low stock
  - very low stock
  - out of stock
  - expired replacement
  - meal gap hints
  - optional meal upgrades

candidate merging:
  - same stock_id should merge
  - same item name should merge if stock_id is blank
  - stock evidence and meal-gap evidence should combine

simple scoring:
  - stock urgency
  - meal usefulness
  - number of meal opportunities supported
  - exact item confidence
  - data-quality confidence

read-only safety metadata

tests

MCP wrapper
```

### Exclude from 1.5D-A

```text
shopping_list.csv
confirmed shopping-list write tools
store-aware recommendations
price-aware recommendations
budget optimisation
quantity prediction
nutrition optimisation
preference learning
automatic meal planning
automatic inventory deduction
automatic waste creation
external recipe APIs
```

---

## Recommended Tool Contract

### Service function

Recommended core service function:

```python
def draft_restock_suggestions(
    include_low_stock: bool = True,
    include_out_of_stock: bool = True,
    include_expired_replacements: bool = True,
    include_meal_gap_candidates: bool = True,
    include_optional_upgrades: bool = True,
    max_suggestions: int = 8,
    max_meal_suggestions: int = 5,
    use_soon_days: int = 3,
    reference_date: str = "",
) -> dict:
    ...
```

### MCP tool name

```text
draft_restock_suggestions
```

### MCP description

```text
Draft read-only restock and shopping-list candidate suggestions from inventory signals and meal-opportunity gaps.

Use this when the user asks what groceries they might need, what to restock, what would improve possible meals, or what shopping-list items could be considered.

This tool does not create shopping-list records, update inventory, deduct stock, log intake, or create waste records.
```

---

## Recommended Response Shape

```json
{
  "tool_name": "draft_restock_suggestions",
  "summary": "Prepared 4 restock suggestion draft(s) from inventory and meal-gap signals. No records were changed.",
  "result_type": "restock_suggestion_draft",
  "status": "success",
  "inputs": {
    "include_low_stock": true,
    "include_out_of_stock": true,
    "include_expired_replacements": true,
    "include_meal_gap_candidates": true,
    "include_optional_upgrades": true,
    "max_suggestions": 8,
    "max_meal_suggestions": 5,
    "use_soon_days": 3,
    "reference_date": ""
  },
  "signals": {
    "stock_attention_signals": [],
    "expired_replacement_signals": [],
    "meal_gap_signals": [],
    "meal_support_signals": [],
    "candidate_merge_signals": [],
    "data_quality_signals": []
  },
  "suggestions": [],
  "warnings": [],
  "next_actions": [],
  "safety": {
    "read_only": true,
    "inventory_mutation_performed": false,
    "intake_mutation_performed": false,
    "consumption_mutation_performed": false,
    "waste_mutation_performed": false,
    "shopping_list_mutation_performed": false,
    "requires_user_confirmation_before_write": true
  },
  "metadata": {
    "version": "1.5D",
    "records_checked": {
      "inventory": 0,
      "intake_history": 0,
      "intake_items": 0,
      "consumption": 0,
      "waste": 0
    },
    "reference_date": "2026-05-19"
  }
}
```

This mirrors the existing planning response philosophy while allowing `suggestions` to be populated.

---

## Recommended Suggestion Object Shape

Each restock suggestion should be evidence-rich.

```json
{
  "item_name": "Rice",
  "candidate_type": "exact_item_restock",
  "suggestion_type": "restock",
  "priority": "high",
  "confidence": "high",
  "score": 72,
  "current_status": "low",
  "source_stock_ids": ["inv_002"],
  "category": "pantry",
  "roles": ["base"],
  "supports_meals": ["Chicken rice bowl", "Salad bowl"],
  "blocking_meal_count": 0,
  "supporting_meal_count": 2,
  "optional_meal_count": 0,
  "evidence_types": ["low_stock", "meal_gap"],
  "reasons": [
    "Item is marked low.",
    "Item supports multiple meal opportunities."
  ],
  "suggested_action": "Consider restocking Rice.",
  "would_create_shopping_list_record": false,
  "requires_user_confirmation_before_write": true
}
```

---

## Candidate Types

Version 1.5D should clearly separate restock candidate types.

### exact_item_restock

An existing inventory item is low, very low, or out.

Example:

```text
Rice is low.
```

### expired_replacement

An existing inventory item is expired and may need replacement.

Example:

```text
Spinach is expired and should not be used as available inventory. Consider replacing it if it is still useful.
```

### meal_gap_restock

An item appears in meal gap hints for possible meals.

Example:

```text
Cheese may improve wraps and pasta meals.
```

### optional_meal_upgrade

An item is not required but would improve one or more meal opportunities.

Example:

```text
Sauce could improve rice bowls or wraps.
```

### generic_role_gap

A useful role is missing, but no exact tracked item is known.

Example:

```text
A vegetable option would improve several meals, but no exact tracked vegetable item was identified.
```

This should be lower confidence than an exact inventory item.

---

## Priority and Confidence

Priority and confidence should stay separate.

### Priority means

```text
How useful or urgent is this restock?
```

### Confidence means

```text
How strongly does the available data support this restock?
```

Examples:

```text
High priority, high confidence:
  Eggs are out, are a known tracked item, and support omelettes.

High priority, medium confidence:
  A protein option could unlock several meals, but no exact item is tracked.

Medium priority, high confidence:
  Cheese is low and improves wraps, but meals are still possible without it.

Low priority, low confidence:
  A generic sauce option might help, but the evidence is weak.
```

---

## Suggested Scoring Model

Keep scoring deterministic and explainable.

```python
score = 0

# Stock urgency
if current_status == "out":
    score += 40
elif candidate_type == "expired_replacement":
    score += 35
elif current_status == "very_low":
    score += 30
elif current_status == "low":
    score += 20

# Meal usefulness
score += blocking_meal_count * 18
score += supporting_meal_count * 10
score += optional_meal_count * 5

# Evidence quality
if exact_inventory_item:
    score += 10

if candidate_type == "generic_role_gap":
    score -= 10

if data_quality_issues:
    score -= 10
```

Priority mapping:

```text
score >= 60 → high
score >= 30 → medium
else → low
```

Confidence mapping:

```text
high:
  exact tracked item, clear stock status, clear food role

medium:
  exact tracked item but weak quantity/expiry data
  or strong meal-gap signal but less complete inventory data

low:
  generic role gap only
  unknown food role
  missing key evidence
```

---

## Recommended Module Architecture

### Lowest-risk implementation

```text
core/restock_helpers.py
  Pure helper logic for restock candidates, merging, scoring, and suggestion formatting.

grocery_service.py
  Add a thin draft_restock_suggestions wrapper:
    - read inventory
    - call build_restock_suggestion_draft
    - return result

mcp_tools/restock_suggestion_tools.py
  Register draft_restock_suggestions tool.

tests/test_draft_restock_suggestions.py
  Service-level tests.
```

This matches the current pattern used by `draft_meal_suggestions`.

### Cleaner long-term architecture

```text
core/planning_helpers.py
  shared safety, warnings, stock status, expiry classification

core/meal_signal_helpers.py
  shared inventory item signal building
  food role inference
  meal template matching
  meal gap signal generation

core/meal_suggestion_service.py
  meal suggestion response construction

core/restock_helpers.py
  restock candidate construction
  restock candidate merging
  restock scoring
  restock suggestion response construction

mcp_tools/meal_suggestion_tools.py
  MCP wrapper only

mcp_tools/restock_suggestion_tools.py
  MCP wrapper only
```

This is more modular and better for continued Version 1.5 signal improvements.

### Practical recommendation

For Version 1.5D, use a hybrid approach:

1. Add `restock_helpers.py`.
2. Add `draft_restock_suggestions` as a thin wrapper in `grocery_service.py`.
3. Reuse `build_meal_suggestion_draft` initially, but use its structured `suggestions[*].gap_hints`, not `restock_hint` prose.
4. Add a small enhancement to gap signals so they preserve enough meal/template context.
5. Avoid a large refactor until after 1.5D is passing.

This avoids over-engineering while keeping the door open for better modularity.

---

## Recommended Internal Flow

```text
draft_restock_suggestions()
↓
read_inventory()
↓
build stock-based restock candidates
↓
build meal suggestion draft using current 1.5C helper
↓
extract structured gap hints from meal suggestions
↓
build meal-gap restock candidates
↓
merge candidates by stock_id / item_name / role
↓
score merged candidates
↓
rank candidates
↓
limit to max_suggestions
↓
return read-only planning response
```

Important rule:

```text
Do not parse restock_hint strings.
Use structured gap_hints and inventory signals instead.
```

---

## Candidate Merge Rules

Restock candidates should merge when they refer to the same real item.

Recommended merge key:

```text
if stock_id exists:
  ("stock_id", stock_id)

else:
  ("item_name", normalized_item_name)
```

For generic role gaps:

```text
("generic_role", role_name)
```

Merged candidates should combine:

```text
evidence_types
reasons
supports_meals
source_stock_ids
highest stock urgency
meal support counts
data-quality issues
```

This prevents duplicated suggestions such as:

```text
Buy rice because it is low.
Buy rice because it supports rice bowls.
```

Instead, return one stronger suggestion:

```text
Rice is low and supports rice bowls.
```

---

## Exact Item vs Generic Role Gap

This is a key architectural decision.

The system should avoid hallucinating specific groceries when the data only supports a role.

Correct:

```text
A vegetable option would improve wraps.
```

Risky:

```text
Buy tomato.
```

Unless tomato exists as a tracked low/out/expired inventory item or appears in a user-provided context.

Recommended rule:

```text
Use exact item names only when they come from inventory records or structured known item signals.
Use generic role names when the system only knows a meal role is missing.
```

---

## Near-Miss Meal Opportunities

Near-miss meal matching is useful but should probably be deferred.

Current meal suggestions only appear when the meal is already possible. That means 1.5D-A will mostly suggest restocks that improve possible meals, not restocks that unlock impossible meals.

Future near-miss logic could answer:

```text
You have wraps, cheese, and lettuce, but no protein.
Restocking a protein option would unlock stronger wrap suggestions.
```

This requires a second type of meal matching:

```text
possible_meal_match:
  required item is available

near_miss_meal_match:
  required item or required role is missing, low, or out
  enough supporting items exist to make the restock useful
```

Recommended decision:

```text
Defer near-miss matching to 1.5E or 1.5D-B unless 1.5D-A is very small.
```

---

## Recommended Tests

### Empty inventory

```text
empty inventory returns success
suggestions is []
warning_type includes no_inventory_items
no mutation metadata remains false
```

### Low stock restock

```text
low item appears as exact_item_restock
priority is at least medium
confidence is high if item and status are clear
```

### Very low outranks low

```text
very_low candidate ranks above low candidate when all else is equal
```

### Out of stock restock

```text
out item appears as restock candidate
out item is not treated as available meal ingredient
```

### Expired replacement

```text
expired item appears as expired_replacement
expired item is not treated as usable inventory
reason warns it should not be consumed
```

### Meal-gap increases priority

```text
an item that is low and appears in multiple meal gap hints ranks above a low item with no meal support
```

### Candidate merging

```text
same item from stock attention and meal gap becomes one merged suggestion
```

### Generic role gap

```text
generic role gap returns a generic suggestion
does not invent a specific food item
confidence is low or medium, not high
```

### max_suggestions

```text
result suggestions length is <= max_suggestions
warning appears when results are limited
```

### Safety

```text
read_only is true
inventory_mutation_performed is false
intake_mutation_performed is false
consumption_mutation_performed is false
waste_mutation_performed is false
shopping_list_mutation_performed is false
requires_user_confirmation_before_write is true
```

### MCP registration

```text
draft_restock_suggestions tool appears
tool returns result_type == restock_suggestion_draft
tool description clearly says no records are changed
```

---

## Documentation Decisions to Record

Version 1.5D should explicitly record the following design decisions.

### Decision 1 — Restock suggestions remain draft-only

Version 1.5D does not create shopping-list records.

### Decision 2 — Shopping-list persistence is deferred

A future shopping-list workflow should have its own lifecycle, schema, write tools, and tests.

### Decision 3 — Structured signals are preferred over prose parsing

Restock logic should use structured `gap_hints`, stock signals, and candidate objects.

It should not parse `restock_hint` text.

### Decision 4 — Meal-aware restock suggestions are more useful than stock-only restock suggestions

Low stock matters more when it supports likely meals.

### Decision 5 — Exact item suggestions and generic role suggestions must be separated

This prevents hallucinated grocery items.

### Decision 6 — Priority and confidence stay separate

A suggestion can be urgent but uncertain.

### Decision 7 — Near-miss meals are deferred

The first implementation should use current possible meal opportunities and their gap hints.

### Decision 8 — Safety metadata is mandatory

Every Version 1.5D response should explicitly state that no mutation occurred.

---

## Proposed 1.5D Implementation Steps

### Step 1 — Add documentation

Create:

```text
docs/version_1_5d_restock_suggestion_architecture.md
```

Include:

```text
purpose
problem being solved
architecture options considered
recommended architecture
response contract
scoring strategy
safety boundaries
tests
future decisions
```

### Step 2 — Improve meal gap signal shape

Enhance existing gap signals with more context while keeping old fields.

Recommended added fields:

```text
template_id
template_name
matched_roles
gap_role
```

Avoid breaking existing tests.

### Step 3 — Add `restock_helpers.py`

Suggested helper functions:

```python
def build_restock_suggestion_draft(...):
    ...

def build_stock_restock_candidates(...):
    ...

def build_expired_replacement_candidates(...):
    ...

def build_meal_gap_restock_candidates(...):
    ...

def merge_restock_candidates(...):
    ...

def score_restock_candidate(...):
    ...

def priority_from_score(...):
    ...

def confidence_from_candidate(...):
    ...
```

### Step 4 — Add service wrapper

In `grocery_service.py`:

```python
def draft_restock_suggestions(...):
    inventory_df = read_inventory()
    return build_restock_suggestion_draft(...)
```

Keep this wrapper thin.

### Step 5 — Add MCP wrapper

Create either:

```text
mcp_tools/restock_suggestion_tools.py
```

or add to an existing suggestion tools module.

Recommended:

```text
mcp_tools/restock_suggestion_tools.py
```

This keeps suggestion tools modular as Version 1.5 grows.

### Step 6 — Add tests

Create:

```text
tests/test_draft_restock_suggestions.py
```

Optionally add MCP registration tests if the project already has them.

### Step 7 — Run full test suite

```powershell
pytest -q
```

### Step 8 — Manual MCP Inspector check

Confirm:

```text
draft_restock_suggestions appears
arguments are descriptive
result_type is restock_suggestion_draft
safety metadata confirms no mutation
suggestions are explainable
```

---

## Recommended Minimal File Changes

```text
Modified:
  grocery_assistant_mcp/core/meal_suggestion_helpers.py
  grocery_assistant_mcp/core/grocery_service.py

Added:
  grocery_assistant_mcp/core/restock_helpers.py
  grocery_assistant_mcp/mcp_tools/restock_suggestion_tools.py
  tests/test_draft_restock_suggestions.py
  docs/version_1_5d_restock_suggestion_architecture.md
```

Optional later cleanup:

```text
Added:
  grocery_assistant_mcp/core/meal_signal_helpers.py
  grocery_assistant_mcp/core/meal_suggestion_service.py

Modified:
  grocery_assistant_mcp/core/meal_suggestion_helpers.py
  grocery_assistant_mcp/core/planning_helpers.py
```

---

## Final Recommendation

Version 1.5D should be implemented as a small but meaningful restock reasoning layer:

```text
draft_restock_suggestions
```

It should:

```text
remain read-only
reuse existing meal suggestion signals
rank restock candidates from both stock status and meal usefulness
merge duplicate candidates
separate exact item candidates from generic role gaps
return strong safety metadata
avoid creating shopping-list records
avoid parsing prose
avoid large refactors unless necessary
```

The strongest architectural move is to treat restock suggestions as another signal transformation:

```text
records
↓
inventory signals
↓
meal signals
↓
gap signals
↓
restock candidate signals
↓
ranked restock drafts
```

This keeps Version 1.5 open-ended and extensible while still giving the project a concrete next deliverable.
