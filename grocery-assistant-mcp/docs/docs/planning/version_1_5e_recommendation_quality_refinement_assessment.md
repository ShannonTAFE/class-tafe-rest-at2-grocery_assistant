# Version 1.5E — Recommendation Quality Refinement Reassessment

**Status:** Proposal / architecture assessment  
**Created:** 2026-05-20  
**Context reviewed:** Version 1.5 roadmap documents, Version 1.5D implementation notes, current service/helper/tool files, and current meal/restock/planning tests  
**Implementation mode:** Planning document only; no code changes in this document

---

## Purpose

This document reassesses the proposed direction for **Version 1.5E — Recommendation Quality Refinement** after reviewing the actual Version 1.5D code files.

The previous high-level recommendation was broadly correct:

```text
Improve recommendation quality before introducing shopping-list writes, feedback logging, or machine-learning recommendation.
```

However, the current code context changes the implementation emphasis.

The strongest Version 1.5E move is not to immediately add many new recommendation features. The strongest move is to make the existing signal and suggestion layer more consistent, reusable, evidence-rich, and easier to test.

Version 1.5E should therefore be a refinement and consolidation patch.

---s

## Executive Decision

Version 1.5E should focus on:

```text
shared signal quality
role inference quality
scoring transparency
confidence honesty
explanation consistency
data-quality tolerance
backward-compatible output enrichment
```

Version 1.5E should not yet introduce:

```text
persistent shopping-list writes
recommendation event logging
feedback logging
preference learning
machine-learning training
nutrition optimisation
budget optimisation
external recipe APIs
automatic meal planning
automatic record mutation
```

The project should stay aligned with the Version 1.5 rule:

```text
Suggestions can be intelligent, but writes must remain explicit.
```

---

## What Changed After Reviewing the Current Code

The earlier proposal suggested adding broad recommendation-quality helpers, score breakdowns, improved role inference, improved templates, and near-miss matching.

After reviewing the code, I would adjust the sequencing.

### Earlier recommendation

```text
Add recommendation-quality helpers and improve scoring/template matching broadly.
```

### Updated recommendation

```text
First consolidate duplicated meal/restock signal primitives, then enrich scoring and explanations.
```

This matters because the current code already has functioning Version 1.5C and Version 1.5D tools. The risk is not that the system lacks a recommendation layer. The risk is that the recommendation layer will become harder to evolve if meal and restock logic continue to duplicate or privately reimplement the same concepts.

---

## Current Baseline Assessment

## Strengths

### 1. The service wrappers are correctly thin

`grocery_service.py` keeps `draft_meal_suggestions` and `draft_restock_suggestions` as thin wrappers around helper-layer functions.

Current flow:

```text
draft_meal_suggestions()
↓
read_inventory()
↓
build_meal_suggestion_draft(...)

draft_restock_suggestions()
↓
read_inventory()
↓
build_restock_suggestion_draft(...)
```

This is a strong design. Version 1.5E should preserve it.

The service layer should not become a ranking or scoring layer.

---

### 2. Version 1.5D successfully uses meal-aware restock reasoning

`restock_helpers.py` already uses `build_meal_suggestion_draft` to inspect meal opportunities and extract meal-gap context.

That means Version 1.5D achieved the important architectural step:

```text
restock suggestions are not just stock reminders
restock suggestions can be informed by possible meals
```

This supports the Version 1.5 philosophy:

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
```

Version 1.5E should improve this chain rather than replace it.

---

### 3. Restock suggestions already have stronger response metadata than meal suggestions

`draft_restock_suggestions` currently returns:

```text
tool_name
summary
result_type
status
inputs
signals
suggestions
warnings
next_actions
safety
metadata
```

This is strong and aligns with the planning-tool response contract.

By contrast, `draft_meal_suggestions` currently returns:

```text
tool_name
summary
result_type
status
inputs
signals
suggestions
warnings
```

It does not yet return response-level `safety`, `metadata`, or `next_actions`.

This should be one of the simplest and highest-value Version 1.5E improvements.

---

### 4. The current tests protect important behavioural boundaries

The meal suggestion tests already cover:

```text
empty inventory
use-soon item creates high-priority suggestion
out-of-stock item is not used as a main ingredient
low-stock item can become a gap hint
expired item is excluded from usable main items
missing expiry data does not block suggestions
max_suggestions is respected
```

The restock tests already cover:

```text
empty inventory
low-stock restock suggestions
out-of-stock restock candidates
expired replacement suggestions
meal-gap priority elevation
optional upgrade filtering
max_suggestions
read-only safety contract
```

This is a good baseline. Version 1.5E should add quality tests without breaking these existing behaviours.

---

## Current Design Gaps

## Gap 1 — Role inference is duplicated

`meal_suggestion_helpers.py` owns:

```text
ROLE_KEYWORDS
CATEGORY_ROLE_MAP
_infer_roles()
```

`restock_helpers.py` imports the role maps and also defines its own `_infer_roles()`.

This duplication is not dangerous yet, but it is the clearest sign that Version 1.5E needs shared signal infrastructure.

Recommended correction:

```text
Create core/meal_signal_helpers.py
Move shared role maps and role inference there
Have both meal_suggestion_helpers.py and restock_helpers.py use it
```

This is better than allowing restock and meal suggestions to drift apart.

---

## Gap 2 — Status and expiry interpretation are split across modules

`planning_helpers.py` already provides shared functions:

```text
normalize_stock_status
safe_parse_date
classify_expiry
days_until
```

`meal_suggestion_helpers.py` still has private versions:

```text
_normalise_status
_parse_date_or_status
```

`restock_helpers.py` already uses `planning_helpers.py` for stock and expiry interpretation.

Recommended correction:

```text
Move meal suggestion status/date interpretation toward planning_helpers.py.
```

This should be done carefully and with tests because meal suggestions currently support aliases such as:

```text
ok
available
empty
out_of_stock
```

The goal is not to change behaviour. The goal is to make one shared interpretation layer.

---

## Gap 3 — Meal suggestions lack safety and metadata blocks

All Version 1.5 planning/suggestion tools should clearly report:

```text
read_only = true
inventory_mutation_performed = false
intake_mutation_performed = false
consumption_mutation_performed = false
waste_mutation_performed = false
shopping_list_mutation_performed = false
requires_user_confirmation_before_write = true
```

`draft_restock_suggestions` already does this.

`draft_meal_suggestions` should be updated in Version 1.5E to include:

```text
next_actions
safety
metadata
```

This should be additive and backward compatible.

Do not remove existing fields.

---

## Gap 4 — Priority and confidence are currently useful but coarse

Meal suggestions currently use string-level scoring:

```text
priority: high / medium / low
confidence: high / medium / low
```

Restock suggestions use a numeric score internally and expose:

```text
score
priority
confidence
```

But neither layer exposes enough detail to explain why the score was assigned.

Recommended correction:

```text
Add score_breakdown fields without replacing existing priority/confidence fields.
```

This should be additive.

Example:

```json
{
  "priority": "medium",
  "confidence": "medium",
  "score": 48,
  "score_breakdown": {
    "availability_score": 20,
    "use_soon_score": 0,
    "template_match_score": 20,
    "gap_penalty": -5,
    "data_quality_penalty": -2,
    "meal_support_score": 15
  }
}
```

This would help both testing and agent explanation.

---

## Gap 5 — Role inference is keyword-based and may create false positives

Current role inference uses direct substring matching.

This is simple and useful, but it can create false positives.

Example risk:

```text
egg keyword may match eggplant
```

Recommended correction:

```text
Use token-aware and phrase-aware matching.
```

This does not require a food ontology.

A simple Version 1.5E-safe approach:

```text
normalise item text
check known multi-word phrases first
tokenise words
match single-word keywords against tokens
allow controlled substring matching only for specific safe cases
```

This can improve quality without adding external dependencies.

---

## Gap 6 — Generic role gaps are useful but need clearer user-facing caution

`draft_restock_suggestions` can already return generic role gaps such as:

```text
vegetable option
protein option
sauce or condiment option
```

This is good because it avoids inventing exact foods.

However, the agent-facing wording should be more explicit:

```text
This is a role-level idea, not a confirmed shopping-list item.
Ask the user what type of protein/vegetable/sauce they prefer.
Do not phrase it as “buy tomato” unless tomato exists in inventory or was supplied by the user.
```

Recommended correction:

```text
Add generic_role_guidance or limitations to generic role gap suggestions.
```

---

## Gap 7 — Near-miss matching is valuable, but should not become full meal suggestion yet

Near-miss matching means identifying meals that are almost possible but blocked by one missing required role.

Example:

```text
You have wraps, lettuce, and cheese, but no clear protein.
A protein option could unlock stronger wrap suggestions.
```

This is valuable for restock intelligence.

But it is risky if exposed as a meal suggestion because the meal is not currently possible.

Recommended Version 1.5E boundary:

```text
Allow near-miss signals only as restock-supporting evidence.
Do not present near-miss meals as normal draft_meal_suggestions unless a separate include_near_miss flag is intentionally added later.
```

This keeps meal suggestions conservative while improving restock quality.

---

## Reassessed Recommendation

The updated Version 1.5E should be split into three internal refinement tracks.

---

# Track 1 — Shared Signal Foundations

## Goal

Create a small shared module for food role and item-signal interpretation.

## Proposed file

```text
grocery_assistant_mcp/core/meal_signal_helpers.py
```

## Responsibilities

```text
ROLE_KEYWORDS
CATEGORY_ROLE_MAP
ROLE_LABELS
MEAL_TEMPLATES, if appropriate
normalise_food_text
tokenise_food_text
infer_food_roles
build_inventory_item_signal
build_inventory_item_signals
build_data_quality_labels_for_item
```

## Why this should come first

Both meal suggestions and restock suggestions depend on the same concepts:

```text
food role
stock availability
expiry status
quantity/serving sufficiency
data quality
```

If these concepts remain split across helpers, future recommendation quality work becomes harder.

---

# Track 2 — Output Contract Alignment

## Goal

Make `draft_meal_suggestions` align more closely with `draft_restock_suggestions` and the planning response pattern.

## Add to `draft_meal_suggestions`

```text
next_actions
safety
metadata
```

## Preserve existing fields

Do not remove or rename:

```text
tool_name
summary
result_type
status
inputs
signals
suggestions
warnings
```

## Suggested metadata

```json
{
  "generated_at": "ISO datetime",
  "version": "1.5E",
  "source_tools": [],
  "records_checked": {
    "inventory": 0,
    "intake_history": 0,
    "intake_items": 0,
    "consumption": 0,
    "waste": 0
  },
  "reference_date": "YYYY-MM-DD"
}
```

## Suggested next actions

If suggestions exist:

```text
Ask which meal idea the user wants to act on
Optionally log a meal only after explicit confirmation
Optionally draft restock suggestions if gaps matter
```

If no suggestions exist:

```text
Add or improve inventory records
Review inventory data quality
Review low-stock or use-soon items
```

---

# Track 3 — Recommendation Quality Enrichment

## Goal

Make suggestions easier to trust and easier to test.

## Additive fields for meal suggestions

```text
score
score_breakdown
match_quality
data_quality
assumption_level
recommendation_risk
evidence_summary
limitations
agent_guidance
```

## Additive fields for restock suggestions

```text
score_breakdown
data_quality
assumption_level
recommendation_risk
evidence_summary
limitations
agent_guidance
```

## Important rule

Do not replace current fields.

Current tests and MCP usage expect fields such as:

```text
priority
confidence
main_items_used
gap_hints
reason
supports_meals
source_signal_types
requires_user_confirmation_before_write
```

Version 1.5E should enrich the response, not rewrite it.

---

## Recommended 1.5E Scope

## Include

```text
create shared meal_signal_helpers.py
deduplicate role inference
reuse planning_helpers for stock/date parsing
add safety and metadata to draft_meal_suggestions
add score_breakdown to meal and restock suggestions
add data_quality / assumption_level / recommendation_risk fields
add evidence_summary and limitations fields
improve role matching with token-aware keyword matching
improve generic role-gap explanation
add tests for recommendation quality and output contract compatibility
```

## Exclude

```text
shopping-list persistence
shopping-list write tools
recommendation-event CSVs
feedback CSVs
preference learning
ML ranking
nutrition ranking
cost ranking
store-aware suggestions
automatic meal logging
automatic inventory deduction
automatic waste creation
external recipe APIs
large recipe/template system
```

---

## Recommended Implementation Sequence

## Step 1 — Add documentation

Create this proposal file:

```text
docs/version_1_5e_recommendation_quality_refinement.md
```

This document should be committed before code implementation.

---

## Step 2 — Add shared signal helper module

Create:

```text
grocery_assistant_mcp/core/meal_signal_helpers.py
```

Move or mirror the stable parts of:

```text
ROLE_KEYWORDS
CATEGORY_ROLE_MAP
ROLE_LABELS
infer_food_roles
safe item text normalisation
```

Initial rule:

```text
Do not change current role outputs unless tests are added first.
```

---

## Step 3 — Update meal_suggestion_helpers.py to use shared helpers

Replace private role inference where safe.

Also consider replacing private status/date parsing with:

```text
normalize_stock_status
classify_expiry
safe_parse_date
days_until
```

from `planning_helpers.py`.

This should be done carefully because status interpretation affects whether an item is considered available, low, out, expired, or unknown.

---

## Step 4 — Update restock_helpers.py to use shared helpers

Remove duplicated `_infer_roles()` from `restock_helpers.py`.

Keep restock-specific candidate merging and scoring inside `restock_helpers.py`.

---

## Step 5 — Add safety and metadata to meal suggestions

Update both normal and empty meal suggestion responses.

Add:

```text
next_actions
safety
metadata
```

Do not remove current response fields.

---

## Step 6 — Add score breakdowns

Start with restock suggestions because they already expose numeric score.

Then add meal suggestion scores.

Suggested restock breakdown:

```text
stock_urgency_score
meal_support_score
exact_item_score
generic_role_penalty
data_quality_penalty
final_score
```

Suggested meal breakdown:

```text
availability_score
use_soon_score
template_match_score
supporting_item_score
gap_penalty
data_quality_penalty
final_score
```

---

## Step 7 — Add explanation fields

For each suggestion, add:

```text
evidence_summary
limitations
agent_guidance
```

Example:

```json
{
  "evidence_summary": [
    "Eggs are available and match the protein role.",
    "Bread is available and can support the meal.",
    "Expiry data is missing, so freshness confidence is limited."
  ],
  "limitations": [
    "Serving sufficiency was not calculated because quantity or unit data is incomplete."
  ],
  "agent_guidance": "Present this as a soft meal idea, not a confirmed meal plan."
}
```

---

## Step 8 — Add quality tests

Create:

```text
tests/test_recommendation_quality.py
```

Test categories:

```text
role inference quality
token-aware keyword matching
meal suggestion metadata and safety
score_breakdown presence
data-quality penalties
confidence separated from priority
generic role gaps stay generic
near-miss signals do not become normal meal suggestions
restock suggestions remain read-only
backward-compatible fields still exist
```

---

## Recommended Tests

## Role inference tests

```text
category protein maps to protein role
rice maps to base role
wraps map to bread_wrap role
spinach maps to vegetable role
unknown item maps to unknown role
eggplant does not become protein only because it contains "egg"
```

## Meal suggestion quality tests

```text
draft_meal_suggestions includes safety and metadata
use-soon still raises priority
missing expiry lowers freshness confidence but does not block suggestion
missing unit adds a limitation
score_breakdown is present
confidence is not high when role inference is weak
expired items remain excluded
out-of-stock items remain excluded
```

## Restock suggestion quality tests

```text
score_breakdown is present
generic role gap has low confidence
generic role gap does not invent exact item name
exact low-stock item remains exact_item_restock
meal-supported restock outranks stock-only restock when evidence is stronger
optional upgrades can still be disabled
safety contract remains unchanged
```

## Backward compatibility tests

```text
existing suggestion fields remain present
existing warning types remain present
existing result_type values remain unchanged
max_suggestions behaviour remains unchanged
```

---

## Should Version 1.5E Add a New MCP Tool?

No.

The current tools are enough:

```text
draft_meal_suggestions
draft_restock_suggestions
review_planning_context
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
```

Version 1.5E should improve the quality of existing tool outputs.

A new MCP tool would likely increase surface area without solving the core issue.

---

## Should Version 1.5E Add Feedback Logging?

No.

Feedback logging is important, but it should come after recommendation outputs are stable.

If the current recommendation schema changes too much after feedback logging is introduced, historical feedback events become harder to interpret.

Recommended sequence:

```text
1.5E — improve suggestion quality and evidence shape
1.6 — confirmed shopping-list workflow or recommendation-event design
1.7+ — feedback-aware ranking
later — ML only if labelled feedback becomes sufficient
```

---

## Should Version 1.5E Add Near-Miss Meal Suggestions?

Not as normal meal suggestions.

Near-miss logic should be treated as restock evidence only.

Safe form:

```text
A protein option could improve or unlock wrap-style meals.
```

Riskier form:

```text
You can make chicken wraps.
```

The second statement should not be produced unless the relevant ingredient is actually available or user-provided.

---

## Suggested File Changes

## Added

```text
docs/version_1_5e_recommendation_quality_refinement.md
grocery_assistant_mcp/core/meal_signal_helpers.py
tests/test_recommendation_quality.py
```

## Modified

```text
grocery_assistant_mcp/core/meal_suggestion_helpers.py
grocery_assistant_mcp/core/restock_helpers.py
grocery_assistant_mcp/core/planning_helpers.py
tests/test_draft_meal_suggestions.py
tests/test_draft_restock_suggestions.py
```

## Probably not modified

```text
grocery_assistant_mcp/core/grocery_service.py
grocery_assistant_mcp/mcp_tools/planning_tools.py
grocery_assistant_mcp/mcp_tools/meal_suggestion_tools.py
```

Unless new optional arguments are introduced, the service and MCP wrappers can remain mostly unchanged.

---

## Refined Recommendation Compared With Previous Proposal

## Keep from previous proposal

```text
Recommendation quality refinement is the correct Version 1.5E target.
Do not introduce ML yet.
Do not introduce shopping-list writes yet.
Improve food role inference.
Improve meal-template matching.
Improve priority and confidence scoring.
Improve generic role-gap explanations.
Improve incomplete-data tolerance.
Improve explanation consistency.
```

## Change from previous proposal

```text
Do not start by adding a broad recommendation_quality_helpers.py abstraction.
First consolidate shared meal/item signal logic.
Make draft_meal_suggestions match the safety/metadata quality of draft_restock_suggestions.
Keep all output changes additive and backward compatible.
Treat near-miss matching as restock evidence, not normal meal suggestions.
Use score breakdowns as explanation/testing support, not as a black-box ranking layer.
```

---

## Final 1.5E Proposal

Version 1.5E should be implemented as:

```text
A backward-compatible recommendation-quality patch that consolidates shared meal/restock signal logic, improves role inference, aligns meal suggestion response metadata with restock suggestions, and adds transparent score/explanation fields.
```

The practical development path should be:

```text
1. Add this documentation.
2. Create shared meal_signal_helpers.py.
3. Deduplicate role inference.
4. Align meal suggestion safety and metadata.
5. Add score_breakdown and evidence fields.
6. Improve generic role-gap guidance.
7. Add recommendation-quality tests.
8. Run pytest -q.
9. Manually inspect draft_meal_suggestions and draft_restock_suggestions in MCP Inspector.
```

This keeps the project within scope while moving the assistant closer to reliable, explainable, personalised grocery intelligence.

The key principle remains:

```text
Improve the quality of advice before expanding the system's ability to act.
```
