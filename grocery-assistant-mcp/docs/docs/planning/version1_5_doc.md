# Version 1.5C — Signal-Based Meal Suggestion Drafts

## Purpose

Version 1.5C introduces basic meal opportunity drafting from current grocery inventory signals.

This version does not attempt full recipe generation, weekly meal planning, nutrition optimisation, or automatic shopping-list creation. Instead, it creates explainable meal suggestion drafts from inventory signals such as item availability, use-soon status, low stock, inferred food roles, and simple meal templates.

The main goal is to begin moving the assistant from simple record lookup toward useful recommendation behaviour while keeping the logic deterministic, transparent, and testable.

## Why meal suggestions come before restock suggestions

A restock-first system risks becoming a simple replacement checklist:

- rice is low, buy rice
- milk is out, buy milk
- eggs are low, buy eggs

That is useful, but limited.

A meal-first signal system can eventually make restock suggestions more meaningful:

- rice is low and supports several possible meals
- cheese is optional but would improve wraps, omelettes, and pasta meals
- tomato is missing, but chicken wraps are still possible without it

This means restocking can later be connected to meal usefulness instead of only inventory status.

## Core function

```python
draft_meal_suggestions(
    include_use_soon=True,
    include_inventory_based=True,
    include_gap_hints=True,
    max_suggestions=5,
    use_soon_days=3,
)
Behaviour

The function:

Reads current inventory.
Builds availability signals.
Builds freshness and use-soon signals.
Infers simple food roles.
Matches available items against simple meal templates.
Adds low/out-of-stock gap hints.
Scores each suggestion by priority and confidence.
Returns a structured recommendation object.
Does not modify any records.
Signal types used
Inventory availability signals

These describe whether an item can be used in a meal.

Examples:

available
low
very_low
out
expired
unknown

Out-of-stock and expired items are not used as main meal ingredients.

Freshness signals

These describe whether an item should be prioritised due to expiry.

Examples:

use-soon
expired
missing expiry date
invalid expiry date

Use-soon items increase meal suggestion priority. Missing or invalid expiry dates lower data confidence but do not block suggestions.

Meal role signals

Items are assigned simple food roles from category and item-name keywords.

Example roles:

protein
base
bread_wrap
vegetable
fruit
dairy
sauce
seasoning
unknown

This role layer helps the assistant reason about meal opportunities without needing a full recipe database.

Meal templates

Version 1.5C uses simple templates rather than full recipes.

Initial templates include:

rice bowl
pasta meal
wrap or sandwich
omelette or eggs
salad bowl

Each template defines a required role, supporting roles, optional roles, and a minimum number of supporting matches.

Gap-tolerant logic

A missing or low optional item should not block a meal suggestion.

For example:

Chicken wraps may still be possible with chicken and wraps even if cheese is low.

Suggestions include:

main_items_used
use_soon_items_used
low_items_used
missing_or_low_items
gap_hints
still_possible_without_missing_items
Priority and confidence

Priority means how useful or urgent the suggestion is.

Confidence means how strongly the available data supports the suggestion.

A suggestion can be high priority but only medium confidence if it uses a use-soon item but has limited supporting ingredient data.

Output shape

The tool returns:

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
Boundaries

Version 1.5C does not:

generate full recipes
write shopping-list records
create meal plans
optimise calories or macros
use external recipe APIs
learn long-term preferences
perform machine learning recommendation

These remain future opportunities.

Completion criteria

Version 1.5C is complete when:

draft_meal_suggestions exists as a service function
the function is read-only
simple food roles are inferred
simple meal templates are matched
expired/out-of-stock items are excluded from main ingredients
low/out-of-stock items can appear as gap hints
use-soon items increase priority
suggestions include priority, confidence, reason, and restock hint
tests cover empty inventory, use-soon items, low-stock gaps, out-of-stock exclusion, expired exclusion, missing expiry data, and max suggestion limits
the MCP tool is registered and inspectable

---

# 7. Future thinking plan

Add this to your roadmap or future plans document.

```md
# Future Direction After Version 1.5C

## Version 1.5D — Restock Draft Suggestions From Meal Gaps

After meal opportunity drafts exist, restock suggestions should be informed by meal usefulness.

Instead of suggesting items only because they are low or out of stock, the assistant should consider whether the item supports current or likely meals.

Example:

- rice is low and supports chicken rice bowls
- cheese is low and improves wraps, omelettes, and pasta meals
- soy sauce is out and would improve rice bowl suggestions

This creates better shopping-list intelligence because groceries are linked to meals rather than isolated inventory rows.

## Version 1.5E — Shopping List Drafts

Once restock suggestions are explainable, the assistant can draft a shopping list.

The shopping list should still be a draft at first. It should not automatically write records unless the user confirms.

Possible structure:

- essential items
- meal-supporting items
- optional improvements
- replacement items
- low-priority pantry items

## Version 1.6 — User Preference and Meal Feedback Signals

The assistant should eventually learn from:

- meals the user actually eats
- meals the user ignores
- repeated purchases
- frequent waste
- disliked suggestions
- preferred meal types
- common staples

This should not require perfect user input. The system should work with partial and imperfect records.

## Version 1.7 — Nutrition-Aware Opportunities

Nutrition should be introduced after meal suggestions and restock logic are stable.

Possible future signals:

- protein opportunity
- fibre opportunity
- vegetable opportunity
- calorie-light option
- higher-energy option
- balanced meal opportunity

These should be presented gently and optionally, not as strict diet rules.

## Version 1.8 — Cost and Waste-Aware Recommendations

Future versions can rank meal suggestions by:

- use-soon priority
- cost efficiency
- waste reduction
- number of available ingredients
- number of missing ingredients
- user enjoyment
- nutrition value

This would move the assistant closer to a practical household food decision system.

## Long-Term Direction

The project should evolve toward a signal-first grocery intelligence layer:

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

The assistant should avoid depending on perfect CSV data. Missing, low-confidence, or incomplete data should reduce confidence rather than breaking the recommendation flow.


---

# Suggested implementation order

Use this order:

```text
1. Add meal_suggestion_helpers.py
2. Add draft_meal_suggestions() to grocery_service.py
3. Add tests/test_draft_meal_suggestions.py
4. Run targeted tests
5. Fix helper logic if needed
6. Run full pytest suite
7. Register MCP tool
8. Test in MCP Inspector
9. Add documentation
10. Commit as Version 1.5C initial implementation