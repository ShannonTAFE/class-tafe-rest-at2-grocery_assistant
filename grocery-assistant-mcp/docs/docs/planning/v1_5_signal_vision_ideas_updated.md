# Version 1.5 Signal Vision Ideas

**Updated:** 2026-05-19  
**Status:** Long-term signal vision with Version 1.5A scope refinement  
**Implementation mode:** Planning and architecture only; no code in this document

---

## Purpose

This document captures the broader signal vision for Version 1.5 and later versions of the Grocery Assistant MCP project.

The aim is not to implement every idea immediately.

The aim is to document the kinds of signals that could eventually help an LLM agent reason over grocery data in a useful, safe, and personalised way.

Version 1.5A should focus only on the first stable part of this vision:

```text
read existing grocery records
convert them into structured planning signals
return confidence, evidence, warnings, and safety metadata
avoid mutation
```

Future Version 1.5 stages can then use those signals to support meal suggestions, restock suggestions, feedback-aware recommendations, and eventually learning over time.

---

## Core Philosophy

Planning signals are not just raw facts.

They are decision-support cues for the agent.

A raw record might say:

```text
food_item: Spinach
stock_status: in_stock
expiry_date: 2026-05-21
```

A planning signal says:

```text
Spinach is available and should be prioritised soon because it expires soon.
The agent may use this for a soft meal-planning suggestion.
The agent should not automatically deduct inventory from this signal.
```

This distinction is central to Version 1.5.

The planning layer should help answer:

```text
What is available?
What is urgent?
What is uncertain?
What is safe to suggest?
What should be avoided?
What would require explicit user confirmation?
```

---

## Source Records Should Stay Clean

The project should avoid turning source CSV files into overloaded feature tables.

Source files should continue to store user state and user events.

Examples:

```text
inventory records
intake records
intake item records
inventory consumption records
waste records
```

Derived features and interpretation should live in the planning layer.

```text
source records
   ↓
derived planning features
   ↓
planning signals
   ↓
agent guidance
   ↓
future recommendation or feedback tools
```

This design keeps the system flexible and makes later learning easier.

---

## Signal Domains

The long-term signal schema should support many domains.

Recommended domains:

```text
inventory
intake
consumption
waste
nutrition
preference
goal
cost
convenience
meal_construction
substitution
data_quality
system
```

## Version 1.5A Domains

Version 1.5A should only implement:

```text
inventory
intake
data_quality
system
```

These are enough to create a useful planning context without overbuilding.

## Future Domains

Later versions can expand into:

```text
consumption
waste
nutrition
preference
goal
cost
convenience
meal_construction
substitution
```

---

## Core Signal Object

Every planning signal should follow a consistent structure.

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
user_fit
flexibility
agent_guidance
limitations
```

## Field Guide

| Field | Purpose |
|---|---|
| `signal_id` | Stable reference within a response. Useful when later recommendations cite supporting signals. |
| `domain` | The area the signal belongs to, such as inventory or intake. |
| `signal_type` | The type of signal, such as use_soon, low_stock, or missing_quantity. |
| `subject` | The item, meal, record, or concept the signal is about. |
| `severity` | How important or urgent the signal is. |
| `polarity` | Whether the signal is positive, negative, neutral, or cautionary. |
| `confidence` | How reliable the signal is. |
| `reason` | Plain-language explanation. |
| `evidence` | Source record fields that support the signal. |
| `data_quality` | Completeness, missing fields, and assumptions. |
| `user_fit` | Optional future fit against preference, goals, cost, enjoyment, and convenience. |
| `flexibility` | Optional future substitution or ingredient-role information. |
| `agent_guidance` | How the LLM agent should use the signal. |
| `limitations` | What the signal should not be used for. |

---

## Planning Response Schema

The planning layer should return a standard response structure.

Recommended shape:

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

This response shape should remain stable across future planning tools.

For example:

```text
review_planning_context
review_low_stock_items
review_use_soon_items
suggest_meals_from_inventory
review_waste_patterns
```

The same structure makes the agent's job easier.

---

## High-Level Signal Families

The long-term signal vision includes these families:

```text
1. Operational inventory signals
2. Expiry and use-soon signals
3. Quantity sufficiency signals
4. Data-quality and leniency signals
5. Nutrition-opportunity signals
6. Goal-alignment signals
7. Performance and long-term food goal signals
8. Preference and enjoyment signals
9. Cost and affordability signals
10. Convenience and effort signals
11. Meal-construction signals
12. Substitution and flexibility signals
13. Behaviour-pattern signals
14. Waste-reduction signals
15. Consumption velocity signals
16. Linked-record integrity signals
17. Conflict and contradiction signals
18. User-confirmation and safety signals
```

Version 1.5A should implement only a small foundation subset.

---

## 1. Operational Inventory Signals

These signals describe the current usable state of inventory.

Examples:

```text
available_inventory
low_stock
very_low_stock
out_of_stock
expired
unknown_stock_status
```

Why they matter:

```text
The agent needs to know what can be used, what is running low, and what should be avoided.
```

Version 1.5A status:

```text
Implement the basic forms of these signals.
```

---

## 2. Expiry and Use-Soon Signals

These signals help reduce waste and improve meal prioritisation.

Examples:

```text
expired
expires_today
use_soon
no_expiry_data
expiry_date_invalid
```

Why they matter:

```text
An item that expires soon may be more important than an item with plenty of shelf life.
```

Version 1.5A status:

```text
Implement expired, use_soon, and no_expiry_data.
```

Future expansion:

```text
waste_risk
repeated_expiry_pattern
avoid_bulk_purchase
```

---

## 3. Quantity Sufficiency Signals

These signals describe whether enough of an item may be available.

Examples:

```text
quantity_known
quantity_missing
servings_known
servings_missing
possibly_insufficient_quantity
sufficient_for_single_meal
```

Why they matter:

```text
A meal suggestion should treat precise serving calculations differently from loose soft suggestions.
```

Version 1.5A status:

```text
Implement missing_quantity and missing_unit only.
```

Future expansion:

```text
servings_sufficient
partial_meal_possible
needs_top_up_ingredient
```

---

## 4. Data-Quality and Leniency Signals

These signals allow the system to work with imperfect user records.

Examples:

```text
missing_quantity
missing_unit
missing_expiry_date
missing_stock_status
invalid_date
low_confidence_estimate
inference_required
```

Why they matter:

```text
User-entered records will not always be complete or perfectly accurate.
The assistant should remain helpful without overclaiming.
```

## Leniency Concept

The system can classify a record as:

```text
complete enough for soft planning
not complete enough for precise nutrition calculation
not complete enough for automatic inventory mutation
```

This is important because an item with missing unit data may still be useful for a suggestion, but not for an exact deduction.

Version 1.5A status:

```text
Implement basic data-quality warnings and confidence levels.
```

---

## 5. Nutrition-Opportunity Signals

These signals identify possible nutrient opportunities.

Examples:

```text
protein_opportunity
fibre_opportunity
vegetable_opportunity
hydration_opportunity
high_sodium_caution
low_confidence_nutrition
```

Why they matter:

```text
The assistant could eventually suggest foods that support nutrition balance.
```

Version 1.5A status:

```text
Defer.
```

Reason:

```text
Nutrition suggestions require careful confidence handling and should not be presented as medical advice.
```

---

## 6. Goal-Alignment Signals

These signals relate grocery planning to user goals.

Examples:

```text
supports_budget_goal
supports_high_protein_goal
supports_waste_reduction_goal
supports_low_effort_goal
supports_meal_prep_goal
```

Why they matter:

```text
The same meal suggestion may be good or poor depending on the user's current goal.
```

Version 1.5A status:

```text
Defer.
```

Future requirement:

```text
A safe and explicit way to represent user goals.
```

---

## 7. Performance and Long-Term Food Goal Signals

These signals relate to future performance, training, or long-term nutrition planning.

Examples:

```text
pre_workout_meal_opportunity
post_workout_protein_opportunity
slow_energy_meal_option
meal_prep_consistency_signal
long_term_goal_alignment
```

Why they matter:

```text
The project could eventually support gradual food goal coaching.
```

Version 1.5A status:

```text
Defer.
```

Safety note:

```text
These should remain general wellness-style planning signals, not medical or clinical advice.
```

---

## 8. Preference and Enjoyment Signals

These signals capture what the user seems to like, avoid, accept, or repeat.

Examples:

```text
frequently_eaten
rarely_eaten
accepted_suggestion_pattern
rejected_ingredient
high_enjoyment_meal
low_enjoyment_meal
would_repeat
```

Why they matter:

```text
A useful grocery assistant should eventually learn what the user actually enjoys.
```

Version 1.5A status:

```text
Defer.
```

Future requirement:

```text
Recommendation events and explicit feedback records.
```

---

## 9. Cost and Affordability Signals

These signals help the system reason about budget.

Examples:

```text
low_cost_meal_opportunity
expensive_item_to_use_well
bulk_purchase_risk
cost_saving_restock
avoid_waste_due_to_cost
```

Why they matter:

```text
A suggestion may be better if it uses existing inventory or avoids unnecessary shopping.
```

Version 1.5A status:

```text
Defer.
```

Future requirement:

```text
Cost fields, purchase history, or user-provided cost preferences.
```

---

## 10. Convenience and Effort Signals

These signals describe how easy or difficult an option may be.

Examples:

```text
low_effort_option
meal_prep_option
quick_weeknight_option
requires_cooking
requires_shopping
high_cleanup_meal
```

Why they matter:

```text
The best suggestion is often not the nutritionally perfect one, but the one the user will actually do.
```

Version 1.5A status:

```text
Defer.
```

---

## 11. Meal-Construction Signals

These signals help identify whether ingredients can form a meal.

Examples:

```text
complete_meal_possible
partial_meal_possible
missing_key_ingredient
protein_available
carb_available
vegetable_available
sauce_or_flavour_available
```

Why they matter:

```text
The assistant should eventually reason about what can actually be cooked from available inventory.
```

Version 1.5A status:

```text
Defer.
```

Reason:

```text
Meal construction requires stronger ingredient-role modelling.
```

---

## 12. Substitution and Flexibility Signals

These signals help avoid brittle meal suggestions.

Examples:

```text
substitution_available
missing_ingredient_not_blocking
similar_ingredient_available
flexible_recipe_candidate
ingredient_optional
```

Why they matter:

```text
A missing small ingredient should not always block a whole meal idea.
```

Version 1.5A status:

```text
Defer, but design the signal schema so this can be added later.
```

---

## 13. Behaviour-Pattern Signals

These signals identify patterns over time.

Examples:

```text
frequent_breakfast_pattern
weekday_low_effort_pattern
repeated_takeaway_pattern
repeated_inventory_item
possible_staple
```

Why they matter:

```text
Learning user behaviour can make suggestions more relevant.
```

Version 1.5A status:

```text
Defer.
```

Reason:

```text
Requires more historical data and careful interpretation.
Frequency does not always mean preference.
```

---

## 14. Waste-Reduction Signals

These signals help prevent food waste.

Examples:

```text
use_soon
expired_before_use
repeated_waste_item
waste_risk
overbuying_pattern
avoid_bulk_purchase
```

Why they matter:

```text
Waste records reveal where planning failed.
```

Version 1.5A status:

```text
Implement use_soon and expired only.
Defer deeper waste-pattern analysis.
```

---

## 15. Consumption Velocity Signals

These signals describe how quickly inventory is used.

Examples:

```text
fast_consumption
slow_consumption
frequently_consumed
stale_inventory
likely_staple
```

Why they matter:

```text
Restock suggestions become better when the system knows what gets used quickly.
```

Version 1.5A status:

```text
Defer.
```

Future requirement:

```text
Reliable inventory consumption records linked to meals or item usage.
```

---

## 16. Linked-Record Integrity Signals

These signals check whether records connect cleanly.

Examples:

```text
stock_id_available
linked_intake_available
orphan_consumption_record
missing_source_record
possible_duplicate_record
```

Why they matter:

```text
Planning quality depends on record integrity.
```

Version 1.5A status:

```text
Implement stock_id_available if useful.
Defer deeper integrity checks.
```

---

## 17. Conflict and Contradiction Signals

These signals identify records that appear inconsistent.

Examples:

```text
expired_but_marked_in_stock
out_of_stock_but_positive_quantity
quantity_zero_but_in_stock
missing_status_but_servings_remaining
```

Why they matter:

```text
The assistant should not over-trust conflicting records.
```

Version 1.5A status:

```text
Optional only if easy.
Otherwise defer.
```

---

## 18. User-Confirmation and Safety Signals

These signals remind the agent about action boundaries.

Examples:

```text
write_requires_confirmation
recommendations_are_not_actions
not_safe_for_automatic_mutation
read_only_context
```

Why they matter:

```text
The agent must understand the difference between suggesting and changing records.
```

Version 1.5A status:

```text
Implement.
```

---

## Version 1.5A Suggested Foundation Signals

Recommended first signal set:

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

This set is strong because it is:

```text
simple
useful
safe
testable
based on existing records
helpful to an LLM agent
```

---

## Signals to Defer Until Later

Defer these until the signal foundation is stable:

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

These are valuable, but they require more historical data, richer schemas, or stable recommendation events.

---

## Practical Scoring Ideas

## Data Quality Score

A simple score can describe whether a record is complete enough for planning.

Conceptual levels:

```text
complete
usable_with_minor_gaps
usable_for_soft_suggestion_only
low_quality
not_usable_for_this_task
```

## Assumption Level

Signals should make assumptions visible.

Conceptual levels:

```text
low assumption
medium assumption
high assumption
```

## Recommendation Risk

Signals should help the agent avoid overconfident advice.

Conceptual levels:

```text
low risk
medium risk
high risk
```

## Confidence

Confidence should be based on evidence quality, not just whether the signal exists.

Examples:

```text
High confidence: expiry date and stock status are clear.
Medium confidence: item exists but quantity is missing.
Low confidence: status is missing and item availability is inferred.
```

---

## Important Design Boundaries

## Suggestions Are Not Actions

A planning signal can support a suggestion.

It cannot perform a write.

## Soft Nutrition Only

Nutrition signals should be future, general, and non-clinical unless the project explicitly defines safe boundaries.

## Imperfect Data Should Not Break Planning

Missing fields should create warnings and lower confidence, not automatically fail the whole response.

## Frequency Does Not Always Mean Preference

A frequently eaten item may be convenient, cheap, or forced by availability. It should not automatically be treated as loved.

## Missing Ingredients Should Not Always Block Meals

Future meal construction should allow substitutions and partial meal possibilities.

---

## Version 1.5 Roadmap

Recommended staged roadmap:

```text
Version 1.5A — Planning signal foundation
Version 1.5B — Low-stock, use-soon, and restock review tools
Version 1.5C — Basic meal suggestion from inventory
Version 1.5D — Recommendation event and feedback logging
Version 1.5E — Preference-aware and feedback-aware ranking
```

This roadmap supports gradual complexity.

---

## Final Philosophy

The signal layer should help the agent reason better without pretending the data is perfect.

The best Version 1.5 signal architecture is:

```text
structured enough to test
flexible enough to grow
safe enough to prevent accidental writes
clear enough for an LLM agent to use
honest enough to expose uncertainty
```

Version 1.5A should therefore focus on a small, reliable set of foundation signals before any complex recommendation logic is built.
