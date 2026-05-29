# Version 1.5E — Recommendation Quality Refinement Implementation Notes

## Implemented capability

Version 1.5E refines the existing read-only recommendation layer rather than adding a new write workflow.

The patch enriches:

```text
draft_meal_suggestions
draft_restock_suggestions
```

with quality metadata that makes recommendations easier for the agent to rank, explain, and present cautiously.

## Main files changed or added

```text
Added:
  grocery_assistant_mcp/core/recommendation_quality_helpers.py
  tests/test_recommendation_quality.py
  docs/version_1_5e_implementation_notes.md

Updated:
  grocery_assistant_mcp/core/meal_suggestion_helpers.py
  grocery_assistant_mcp/core/restock_helpers.py
```

## Scope decision

Version 1.5E remains read-only.

It does not:

```text
create shopping-list records
update inventory
log intake
deduct stock
create waste records
save recommendation events
save feedback
train a machine-learning model
```

## Why this patch comes before feedback learning

The recommendation outputs need to be stable and evidence-rich before feedback logging becomes useful.

If future feedback records are stored, each event should be able to reference why the suggestion was made. This patch prepares for that by adding consistent fields such as:

```text
score
score_breakdown
data_quality
assumption_level
recommendation_risk
evidence_summary
limitations
agent_guidance
```

## Meal suggestion improvements

`draft_meal_suggestions` now includes response-level planning metadata similar to other Version 1.5 planning tools:

```text
next_actions
safety
metadata
```

Each meal suggestion is enriched with:

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

Existing response fields are preserved for compatibility:

```text
meal_name
template_id
template_name
matched_roles
suggestion_type
priority
confidence
main_items_used
use_soon_items_used
low_items_used
missing_or_low_items
gap_hints
still_possible_without_missing_items
reason
restock_hint
```

## Restock suggestion improvements

`draft_restock_suggestions` now uses Version 1.5E quality helpers while preserving the Version 1.5D response shape.

Each restock suggestion is enriched with:

```text
score_breakdown
data_quality
assumption_level
recommendation_risk
evidence_summary
limitations
agent_guidance
```

Existing restock fields are preserved:

```text
item_name
suggestion_type
candidate_type
priority
confidence
score
current_status
category
roles
source_stock_ids
source_signal_types
supports_meals
blocking_meal_count
supporting_meal_count
optional_meal_count
reasons
reason
suggested_action
would_create_shopping_list_record
requires_user_confirmation_before_write
```

## Shared quality helper

The new helper file is:

```text
grocery_assistant_mcp/core/recommendation_quality_helpers.py
```

It centralises:

```text
food role inference metadata
role confidence
quality-level classification
assumption-level classification
recommendation-risk classification
meal score breakdowns
restock score breakdowns
evidence summaries
limitations
agent guidance
```

This reduces the risk of meal and restock logic drifting apart as Version 1.5 grows.

## Design principle

Priority and confidence remain separate.

```text
priority = how useful or urgent the suggestion appears
confidence = how strongly the current records support the suggestion
```

The new `score_breakdown` field gives the agent and tests more insight into why a suggestion received its priority.

## Testing

New tests cover:

```text
role inference evidence metadata
meal suggestion safety metadata
meal suggestion quality fields
empty inventory safety metadata
restock score breakdown fields
generic role gaps remaining low-confidence
no shopping-list write behaviour
```

Recommended check:

```powershell
pytest -q
```

## Manual MCP Inspector checks

Inspect:

```text
draft_meal_suggestions_tool
draft_restock_suggestions_tool
```

Confirm that:

```text
status is success
existing fields still appear
new quality fields appear
safety.read_only is true
mutation flags are false
shopping-list writes are not performed
```

## Future direction after 1.5E

Once these quality fields are stable, later versions can safely consider:

```text
more meal templates
near-miss meal unlock logic
non-persistent draft_shopping_list
recommendation event logging
explicit user feedback logging
preference-aware ranking
```

Machine learning should still wait until enough labelled recommendation feedback exists.
