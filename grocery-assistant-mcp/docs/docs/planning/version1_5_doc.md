# Version 1.5 — Planning Intelligence and Signal-Based Recommendations

**Status:** Version 1.5A, 1.5B, 1.5C, and 1.5D implemented and tested; ready for final commit  
**Last updated:** 2026-05-19  
**Mode:** Read-only planning, recommendation drafts, and decision support

---

## Purpose

Version 1.5 moves the Grocery Assistant MCP project from simple record access toward safe planning intelligence.

The purpose of this version is to help an LLM agent reason from grocery records without silently changing records.

Version 1.5 planning tools may:

```text
review
summarise
rank
suggest
draft
explain
warn
```

They must not silently mutate:

```text
inventory records
intake records
intake item records
inventory consumption records
waste records
shopping list records
```

Any write action should continue to route through explicit, tested write tools and should require clear user intent.

---

## Core Design Rule

Every Version 1.5 planning tool should answer:

```text
What does the agent need to know before giving advice?
```

It should not answer:

```text
What should the system automatically change?
```

This keeps Version 1.5 as a decision-support layer rather than an automation layer.

---

## Version 1.5 Architecture

The planning intelligence path is:

```text
source CSV records
↓
service-layer read functions
↓
planning and recommendation helpers
↓
structured planning signals
↓
draft suggestions / warnings / next actions
↓
LLM agent explanation
↓
explicit user confirmation before any write
```

Source records should remain clean. They store user state and user events.

Derived planning signals should be generated at runtime rather than stored directly into the source CSV files unless a future version explicitly designs a signal-history store.

---

## Completed Version 1.5 Stages

## Version 1.5A — Planning Signal Foundation

### Goal

Create the reusable planning layer before building individual suggestion tools.

### Main deliverable

```text
review_planning_context
```

### Purpose

`review_planning_context` gives the agent a structured overview of the user's grocery context before it suggests anything.

It can expose:

```text
inventory signals
recent intake context
data-quality signals
warnings
safe next actions
read-only safety metadata
records checked metadata
```

### Key implementation ideas

Version 1.5A separates planning logic from direct grocery write logic.

Recommended module responsibilities:

```text
core/planning_helpers.py
  Small reusable functions for interpreting records and creating signals.

core/planning_service.py
  Builds planning responses by reading records, generating signals, adding warnings,
  and preserving safety metadata.

mcp_tools/planning_tools.py
  Thin MCP wrappers that delegate to the service layer.
```

### Boundary

Version 1.5A does not recommend meals, create shopping lists, deduct inventory, or log intake. It only prepares planning context.

---

## Version 1.5B — Focused Inventory Planning Reviews

### Goal

Create focused read-only review tools that reuse the Version 1.5A planning signal layer.

### Completed focused tools

```text
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
```

### Purpose

These tools allow the agent to ask narrower planning questions without manually parsing the full planning context each time.

### Tool responsibilities

```text
review_low_stock_items
  Reviews low, very low, out-of-stock, and related stock-attention signals.

review_use_soon_items
  Reviews expiry-related signals such as use-soon, expired, missing expiry,
  and invalid expiry data.

review_inventory_data_quality
  Reviews inventory data-quality signals such as missing or invalid fields.
```

### Boundary

Version 1.5B tools are review tools, not recommendation tools.

They should return structured signals, warnings, safety metadata, and next-action guidance. They should not create shopping-list rows, update inventory, infer corrections automatically, or deduct stock.

---

## Version 1.5C — Signal-Based Meal Suggestion Drafts

### Goal

Create basic meal opportunity drafts from current inventory signals.

### Main deliverable

```text
draft_meal_suggestions
```

### Why meal suggestions came before restock suggestions

The project considered whether restock suggestions should come before meal suggestions.

The final decision was to build meal opportunity drafts first because restocking is more useful when it is connected to what the user might actually eat.

A restock-first system can become a simple checklist:

```text
rice is low → buy rice
milk is out → buy milk
eggs are low → buy eggs
```

A meal-first signal system can later produce more useful restock reasoning:

```text
rice is low and supports several possible meals
cheese is optional but would improve wraps, omelettes, and pasta meals
tomato is missing, but chicken wraps are still possible without it
```

This makes future shopping suggestions meal-aware rather than purely stock-status-driven.

### Core function

```python
draft_meal_suggestions(
    include_use_soon=True,
    include_inventory_based=True,
    include_gap_hints=True,
    max_suggestions=5,
    use_soon_days=3,
)
```

### Behaviour

The function:

```text
reads current inventory
builds availability signals
builds freshness and use-soon signals
infers simple food roles
matches available items against simple meal templates
adds low/out-of-stock gap hints
scores each suggestion by priority and confidence
returns a structured recommendation object
does not modify any records
```

### Signal types used

#### Inventory availability signals

These describe whether an item can be used in a meal.

Examples:

```text
available
low
very_low
out
expired
unknown
```

Out-of-stock and expired items should not be used as main meal ingredients.

#### Freshness signals

These describe whether an item should be prioritised because of expiry.

Examples:

```text
use_soon
expired
missing_expiry_date
invalid_expiry_date
```

Use-soon items increase meal suggestion priority. Missing or invalid expiry data may lower confidence but should not block meal suggestions.

#### Meal role signals

Items are assigned simple food roles from category and item-name keywords.

Example roles:

```text
protein
base
bread_wrap
vegetable
fruit
dairy
sauce
seasoning
unknown
```

This role layer lets the assistant reason about meal opportunities without requiring a full recipe database.

### Initial meal templates

Version 1.5C uses simple meal templates rather than full recipes.

Initial templates include:

```text
rice bowl
pasta meal
wrap or sandwich
omelette or eggs
salad bowl
```

Each template defines:

```text
required role
supporting roles
optional roles
minimum supporting matches
```

### Gap-tolerant logic

A missing or low optional item should not block a meal suggestion.

Example:

```text
Chicken wraps may still be possible with chicken and wraps even if cheese is low.
```

Meal suggestions may include:

```text
main_items_used
use_soon_items_used
low_items_used
missing_or_low_items
gap_hints
still_possible_without_missing_items
priority
confidence
reason
restock_hint
```

### Priority and confidence

Priority means:

```text
How useful or urgent is this suggestion?
```

Confidence means:

```text
How strongly does the available data support this suggestion?
```

A suggestion can be high priority but medium confidence if it uses a use-soon item but has limited supporting ingredient data.

### Output shape

```json
{
  "tool_name": "draft_meal_suggestions",
  "summary": "Prepared meal suggestion drafts from current inventory signals. No records were changed.",
  "result_type": "meal_suggestion_draft",
  "status": "success",
  "inputs": {},
  "signals": {
    "inventory_signals": [],
    "meal_role_signals": [],
    "meal_match_signals": [],
    "gap_signals": [],
    "data_quality_signals": []
  },
  "suggestions": [],
  "warnings": []
}
```

### Boundary

Version 1.5C does not:

```text
generate full recipes
write shopping-list records
create meal plans
optimise calories or macros
use external recipe APIs
learn long-term preferences
perform machine-learning recommendation
log intake
deduct inventory
```

---

## Version 1.5D — Restock and Shopping-List Draft Suggestions

### Goal

Create read-only restock suggestion drafts from inventory urgency and meal-opportunity gaps.

### Main deliverable

```text
draft_restock_suggestions
```

### Purpose

`draft_restock_suggestions` helps the agent explain which items may be worth restocking and why.

The tool is intentionally not a shopping-list write tool. It prepares shopping-list-shaped suggestions that still require user confirmation before any future write workflow.

### Why restock suggestions use meal gaps

A stock-only restock tool can become a simple checklist:

```text
rice is low → buy rice
milk is out → buy milk
eggs are low → buy eggs
```

Version 1.5D improves this by connecting restock candidates to meal usefulness:

```text
rice is low and supports several possible meals
a vegetable option would improve wraps and salad bowls
eggs are out and would unlock omelette-style meal opportunities
```

This makes restock suggestions more useful than raw stock-status reminders.

### Core function

```python
draft_restock_suggestions(
    include_low_stock=True,
    include_out_of_stock=True,
    include_expired_replacements=True,
    include_meal_gap_candidates=True,
    include_optional_upgrades=True,
    max_suggestions=8,
    max_meal_suggestions=5,
    use_soon_days=3,
)
```

### Behaviour

The function:

```text
reads current inventory
reuses planning and meal-suggestion signal logic
builds stock-based restock candidates
builds expired replacement candidates
builds meal-gap restock candidates
supports generic role-gap suggestions when no exact tracked item exists
merges duplicate candidates
scores and ranks candidates by urgency and meal usefulness
returns structured restock suggestion drafts
does not modify any records
```

### Signal types used

#### Stock attention signals

These describe inventory items that may need attention because they are low, very low, or out of stock.

Examples:

```text
low_stock
very_low_stock
out_of_stock
```

#### Expired replacement signals

These describe items that should not be treated as usable ingredients but may need replacement.

Examples:

```text
expired_replacement
```

#### Meal gap signals

These describe missing, low, or unavailable items that affect meal opportunities.

Useful meal-gap fields include:

```text
food_item
stock_id
gap_type
roles
gap_role
requiredness
meal_name
template_id
template_name
```

The important design decision is that restock suggestions should use structured meal-gap signals, not parse human-readable `restock_hint` strings.

#### Generic role gaps

When a meal could benefit from a role but no exact tracked item exists, the tool may suggest a generic role candidate instead of inventing a specific item.

Example:

```text
vegetable option
```

This keeps recommendations honest when the inventory data is incomplete.

### Candidate types

Restock suggestions may use these candidate types:

```text
exact_item_restock
expired_replacement
generic_role_gap
optional_meal_upgrade
```

### Priority and confidence

Priority means:

```text
How useful or urgent is this restock suggestion?
```

Confidence means:

```text
How strongly does the available data support this suggestion?
```

A suggestion can be high priority but medium confidence if it appears useful but depends on incomplete inventory or meal-gap data.

### Output shape

```json
{
  "tool_name": "draft_restock_suggestions",
  "summary": "Prepared restock suggestion drafts from inventory and meal-gap signals. No records were changed.",
  "result_type": "restock_suggestion_draft",
  "status": "success",
  "inputs": {},
  "signals": {
    "stock_restock_signals": [],
    "expired_replacement_signals": [],
    "meal_gap_restock_signals": [],
    "generic_role_gap_signals": [],
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
    "waste_mutation_performed": false,
    "shopping_list_mutation_performed": false,
    "requires_user_confirmation_before_write": true
  }
}
```

### Boundary

Version 1.5D does not:

```text
create shopping-list records
update inventory
reduce inventory quantities
log intake
create waste records
optimise budget
optimise nutrition
predict exact purchase quantities
choose stores or prices
```

The tool drafts possible restocks. It does not decide that the user definitely wants to buy them.

### Key implementation decision

Version 1.5D keeps shopping-list persistence out of scope.

A future shopping-list workflow should have its own confirmed write lifecycle, such as:

```text
drafted → confirmed → active → bought / skipped / removed
```

Until that exists, 1.5D should remain a read-only decision-support tool.

---

## Current Version 1.5 Tool Set

The active Version 1.5 planning/suggestion tools are:

```text
review_planning_context
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
draft_meal_suggestions
draft_restock_suggestions
```

All of these should remain read-only.

---

## Testing and Closeout Expectations

Version 1.5A should be covered by:

```text
planning helper tests
planning service response-shape tests
planning context contract tests
no-mutation tests
MCP Inspector checks
```

Version 1.5B should be covered by focused review tests for:

```text
low-stock review
use-soon review
inventory data-quality review
empty result handling
filter behaviour
read-only safety metadata
```

Version 1.5C should be covered by tests for:

```text
empty inventory
use-soon item creates high-priority meal suggestion
out-of-stock items are excluded from main ingredients
expired items are excluded from main ingredients
low-stock items can appear as gap hints
missing expiry data does not block suggestions
max_suggestions is respected
```

Version 1.5D should be covered by tests for:

```text
empty inventory
low-stock restock drafts
out-of-stock restock drafts
expired replacement drafts
meal-gap priority elevation
optional upgrade filtering
generic role-gap suggestions
max_suggestions is respected
read-only safety metadata
no mutation of inventory, intake, consumption, waste, or shopping-list records
```

Final closeout check:

```powershell
pytest -q
```

Manual MCP Inspector checks should confirm that each planning tool appears and returns:

```text
status: success
stable result_type
signals block
warnings block
read-only / no-mutation behaviour
```

---

## Next Recommended Stage

The next recommended Version 1.5 stage is:

```text
Version 1.5E — Recommendation quality refinement
```

This should improve the signal quality behind meal and restock suggestions before introducing shopping-list writes.

Useful 1.5E directions include:

```text
better food role inference
better meal-template matching
better priority and confidence scoring
better generic role-gap explanations
better handling of incomplete or messy inventory data
more consistent explanation text for agent-facing responses
```

The next major write-capable stage should likely be:

```text
Version 1.6 — Confirmed shopping-list workflow
```

That future version can design persistent shopping-list records and explicit user-confirmed shopping-list write tools.

---

## Long-Term Direction

The project should continue evolving toward a signal-first grocery intelligence layer:

```text
records
↓
signals
↓
meal opportunities
↓
meal gaps
↓
restock suggestions
↓
shopping-list drafts
↓
user feedback
↓
better future recommendations
```

The assistant should avoid depending on perfect CSV data. Missing, low-confidence, or incomplete data should reduce confidence rather than breaking the recommendation flow.

---

## Documentation Notes

The detailed planning/proposal/patch documents for Version 1.5A and 1.5B can be moved to archive once their key decisions are represented in this consolidated Version 1.5 document.

Keep the Version 1.5D restock suggestion architecture investigation document active while recommendation quality is still evolving. It records the reasoning behind meal-aware restock suggestions, generic role gaps, and the decision to defer persistent shopping-list writes.

Keep this document as the active Version 1.5 overview and closeout reference.
