# Version 1.5 Draft Implementation Plan

## Version 1.5A — Planning Architecture Foundation

### Goal

Create the foundation for all planning tools before building individual suggestions.

This stage defines:

```text
Where planning logic lives
What a planning response looks like
How we prove planning tools do not mutate data
How MCP wrappers expose planning functions
```

### We would create

```text
grocery_assistant_mcp/core/planning_service.py
tests/test_planning_service.py
grocery_assistant_mcp/mcp_tools/planning_tools.py
```

Maybe also:

```text
grocery_assistant_mcp/core/planning_helpers.py
```

### Main decisions

We need to decide a common response shape, probably something like:

```python
{
    "summary": "...",
    "signals_used": [],
    "recommendations": [],
    "warnings": [],
    "next_actions": [],
    "metadata": {
        "inventory_mutation_performed": False,
        "intake_mutation_performed": False,
        "requires_user_confirmation_before_write": True,
    },
}
```

### Why this comes first

Without this stage, every planning tool may return a different structure. That would make the agent harder to guide and the tests harder to maintain.

### Definition of done

```text
Planning service module exists.
Planning response structure is agreed.
Shared helper functions exist.
Tests prove planning helpers do not write to CSV.
Documentation explains Version 1.5 as suggestion-only.
```

---

## Version 1.5B — Inventory Attention Review

### Goal

Give the agent a clean way to understand which inventory items need attention.

This is the safest first real planning capability because it is mostly factual, not creative.

### Tool candidate

```text
review_low_stock_items
```

### It should identify

```text
low stock items
very low stock items
out-of-stock items
expired items
soon-to-expire items
possibly unknown-status items
```

### Why this comes before meal suggestions

Meal suggestions depend on knowing which items are safe, available, low, expired, or useful soon.

If we build this first, later tools can reuse it.

### Example output

```python
{
    "summary": "There are 6 inventory items that may need attention.",
    "low_stock_items": [...],
    "very_low_items": [...],
    "out_of_stock_items": [...],
    "expired_items": [...],
    "use_soon_items": [...],
    "warnings": [
        "Expired items should not be suggested as usable meal ingredients."
    ],
    "metadata": {
        "inventory_mutation_performed": False
    }
}
```

### Definition of done

```text
review_low_stock_items works in service layer.
MCP tool wrapper exposes it.
Tests cover stock_status categories.
Tests cover expiry_date behaviour.
Tests prove no inventory mutation.
MCP Inspector example works.
Curl example works.
```

---

## Version 1.5C — Restock Suggestions

### Goal

Move from factual inventory review to ranked recommendation.

### Tool candidate

```text
suggest_restock_items
```

### It should use

```text
low stock status
very low status
out-of-stock status
expired status
staple-like items
recent consumption if useful
recent intake if useful
notes field if useful
```

### Important design point

Out-of-stock items are not simply “missing.” In your project, keeping out-of-stock records can help preserve memory of common staples and lower-priority items.

So this tool should distinguish:

```text
urgent restock
normal restock
optional restock
do not restock unless wanted
```

### Example output

```python
{
    "summary": "3 restock suggestions found.",
    "restock_suggestions": [
        {
            "food_item": "Eggs",
            "priority": "high",
            "reason": "Marked very_low and useful across common meals.",
            "source_signals": ["stock_status", "recent_intake"]
        },
        {
            "food_item": "Rice",
            "priority": "medium",
            "reason": "Marked out and appears to be a pantry staple.",
            "source_signals": ["stock_status", "category"]
        }
    ],
    "metadata": {
        "shopping_list_mutation_performed": False,
        "requires_user_confirmation_before_write": True
    }
}
```

### Definition of done

```text
suggest_restock_items ranks items.
Priority rules are documented.
Tests cover high, medium, and low priority.
Tests prove no shopping list file is created.
MCP Inspector example works.
Curl example works.
```

---

## Version 1.5D — Recent Intake Pattern Review

### Goal

Give the agent a structured view of recent eating patterns before suggesting meals.

### Tool candidate

```text
review_recent_intake_patterns
```

### It should answer

```text
What meals has the user eaten recently?
Which meal types are represented?
Are meals repetitive?
Are nutrition estimates available?
Are there obvious gaps or unknowns?
```

### Important boundary

This should not become a medical or nutrition-coaching engine.

It should stay descriptive:

```text
You have recently logged several pasta-based dinners.
Breakfast entries are sparse.
Protein estimates are often missing.
```

Not:

```text
You should follow this diet plan.
```

### Example output

```python
{
    "summary": "Recent intake shows repeated pasta-based dinners.",
    "date_range": {
        "start_date": "2026-05-11",
        "end_date": "2026-05-18"
    },
    "recent_meals": [...],
    "patterns": [
        {
            "pattern": "Repeated dinner type",
            "detail": "Pasta appears multiple times in recent dinners."
        }
    ],
    "suggestion_guidance": [
        "Consider suggesting a non-pasta dinner if inventory allows."
    ],
    "metadata": {
        "intake_mutation_performed": False
    }
}
```

### Definition of done

```text
review_recent_intake_patterns summarizes recent intake.
Date range handling is tested.
Empty intake handling is tested.
Pattern outputs are simple and descriptive.
Tests prove no intake mutation.
MCP Inspector example works.
Curl example works.
```

---

## Version 1.5E — Meal Suggestions from Inventory

### Goal

Suggest possible meals grounded in actual inventory.

### Tool candidate

```text
suggest_meals_from_inventory
```

### This is the first more complex planning tool

It should combine:

```text
available inventory
expired item exclusion
use-soon item preference
low-stock caution
optional missing ingredients
recent intake avoidance
```

### Important boundary

This tool should suggest meals, not log them.

The roadmap already says Version 1.4 owns `add_meal_with_items` and `add_meal_with_inventory_items`, and Version 1.4C only deducts inventory when the request explicitly uses inventory-linked items.

So Version 1.5 meal suggestions should point toward those tools but not call them.

### Example output

```python
{
    "meal_suggestions": [
        {
            "meal_name": "Chicken rice bowl",
            "confidence": "high",
            "uses_inventory_items": [
                {
                    "stock_id": "inv_002",
                    "food_item": "Chicken breast"
                },
                {
                    "stock_id": "inv_006",
                    "food_item": "Rice"
                }
            ],
            "missing_optional_items": ["sauce", "fresh greens"],
            "avoid_items": ["expired yoghurt"],
            "reason": "Uses available protein and pantry stock.",
            "can_log_with_inventory_items": True,
            "requires_user_confirmation_before_write": True
        }
    ],
    "metadata": {
        "inventory_mutation_performed": False,
        "intake_mutation_performed": False
    }
}
```

### Definition of done

```text
suggest_meals_from_inventory returns grounded suggestions.
Expired items are excluded.
Low-stock items are handled carefully.
Recent meal repetition can be avoided.
Suggestions include reasons and confidence.
Tests prove no inventory or intake mutation.
MCP Inspector example works.
Curl example works.
```

---

## Version 1.5F — Next Meal Suggestion

### Goal

Create a user-facing planning shortcut for:

```text
What should I eat next?
```

### Tool candidate

```text
suggest_next_meal
```

### Relationship to previous tools

This should probably be an orchestration-style planning function.

It can use the same logic as:

```text
review_low_stock_items
review_recent_intake_patterns
suggest_meals_from_inventory
```

But return fewer, more direct recommendations.

### Example output

```python
{
    "recommended_next_meal": {
        "meal_name": "Chicken rice bowl",
        "meal_type": "dinner",
        "reason": "Uses available inventory and avoids repeating recent pasta meals.",
        "confidence": "high",
        "can_log_with_inventory_items": True
    },
    "alternatives": [...],
    "metadata": {
        "requires_user_confirmation_before_write": True,
        "inventory_mutation_performed": False,
        "intake_mutation_performed": False
    }
}
```

### Definition of done

```text
suggest_next_meal returns one main recommendation.
Alternatives are optional.
Meal type input is supported.
Recent intake and inventory signals are considered.
Tests prove no mutation.
MCP Inspector example works.
Curl example works.
```

---

## Version 1.5G — Draft Shopping List

### Goal

Produce a non-persistent shopping list draft from planning signals.

### Tool candidate

```text
draft_shopping_list
```

### Important boundary

This should not create `user_shopping_list.csv` yet.

Your future plans mention possible shopping list files and tools, but they are still future design questions.

So in Version 1.5, this should only return a draft.

### It can include items from

```text
low stock review
restock suggestions
meal suggestion missing ingredients
expired replacement candidates
```

### Example output

```python
{
    "shopping_list_draft": [
        {
            "food_item": "Eggs",
            "priority": "high",
            "reason": "Marked very_low.",
            "source": "restock_suggestion"
        },
        {
            "food_item": "Spinach",
            "priority": "medium",
            "reason": "Optional missing item for suggested meals.",
            "source": "meal_suggestion"
        }
    ],
    "metadata": {
        "shopping_list_mutation_performed": False,
        "requires_user_confirmation_before_write": True
    }
}
```

### Definition of done

```text
draft_shopping_list returns a structured draft.
No shopping list CSV is created.
No inventory records are changed.
Priorities are documented.
Tests prove no mutation.
MCP Inspector example works.
Curl example works.
```

---

## Version 1.5H — Food Waste Pattern Review

### Goal

Review waste records for simple planning signals.

### Tool candidate

```text
review_food_waste_patterns
```

### Why I would leave this later in 1.5

Waste pattern review may depend on how detailed and consistent your waste records are.

This should come after the easier planning tools are stable.

### It should answer

```text
What items are commonly wasted?
Are certain categories wasted more?
Are items expiring before use?
Are there inventory planning suggestions?
```

### Example output

```python
{
    "summary": "Vegetables appear most often in recent waste records.",
    "waste_patterns": [
        {
            "pattern": "Repeated vegetable waste",
            "detail": "Leafy greens appear multiple times in waste records."
        }
    ],
    "planning_suggestions": [
        "Consider buying smaller quantities of leafy greens."
    ],
    "metadata": {
        "waste_mutation_performed": False
    }
}
```

### Definition of done

```text
review_food_waste_patterns summarizes waste records.
Empty waste history is handled.
Pattern summaries are simple and non-judgmental.
Tests prove no mutation.
MCP Inspector example works.
Curl example works.
```

---

## Recommended Deep-Dive Order

I would deep dive in this exact order:

```text
1. Version 1.5A — Planning architecture foundation
2. Version 1.5B — Inventory attention review
3. Version 1.5C — Restock suggestions
4. Version 1.5D — Recent intake pattern review
5. Version 1.5E — Meal suggestions from inventory
6. Version 1.5F — Next meal suggestion
7. Version 1.5G — Draft shopping list
8. Version 1.5H — Food waste pattern review
```

The logic is:

```text
Foundation first
Inventory signals second
Restock planning third
Intake context fourth
Meal planning fifth
Next-meal shortcut sixth
Shopping list draft seventh
Waste intelligence last
```

---

## Suggested Commit Rhythm

Each stage should be its own commit or small set of commits.

Example:

```text
v1.5a planning service foundation
v1.5b add inventory attention review
v1.5c add restock suggestion planning
v1.5d add recent intake pattern review
v1.5e add meal suggestions from inventory
v1.5f add next meal planning tool
v1.5g add shopping list draft planning
v1.5h add waste pattern review
v1.5 docs and closeout
```

For our next deep dive, I would start with:

```text
Version 1.5A — Planning architecture foundation
```
