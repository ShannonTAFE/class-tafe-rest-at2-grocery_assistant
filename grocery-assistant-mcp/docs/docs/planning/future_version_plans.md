# Future Version Plans

**Last updated:** 2026-05-19  
**Status:** Active future planning document

---

## Purpose

This file records ideas intentionally deferred beyond the current implemented baseline.

The project has now completed the first Version 1.5 planning-intelligence stages:

```text
Version 1.5A — planning signal foundation
Version 1.5B — focused inventory planning reviews
Version 1.5C — signal-based meal suggestion drafts
```

Future work should build on this signal-first foundation instead of bypassing it.

---

## Current Direction

The preferred intelligence sequence is:

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
feedback
↓
learning over time
```

This means future restock and shopping-list suggestions should be informed by meal usefulness, not only by stock status.

---

# Version 1.5D — Restock Draft Suggestions From Meal Gaps

## Goal

Create read-only restock suggestions informed by:

```text
low-stock inventory signals
out-of-stock inventory signals
expired replacement signals
meal opportunity gaps from draft_meal_suggestions
usefulness across multiple meal opportunities
```

## Why this comes after meal suggestions

A pure restock system can become a checklist:

```text
rice is low → buy rice
milk is out → buy milk
eggs are low → buy eggs
```

A meal-aware restock system can explain why an item matters:

```text
rice is low and supports chicken rice bowls and stir-fry meals
cheese is low and would improve wraps, omelettes, and pasta meals
soy sauce is out and would improve rice bowl suggestions
```

## Candidate tool

```text
draft_restock_suggestions
```

## Important boundary

This tool should not write to a shopping list yet.

It should return a draft with:

```text
food_item
priority
reason
source_signals
related_meal_opportunities
required_or_optional
confidence
requires_confirmation_before_write
```

---

# Version 1.5E — Shopping List Drafts

## Goal

Create a non-persistent shopping-list draft from planning signals.

## Candidate tool

```text
draft_shopping_list
```

## Inputs may include

```text
restock suggestions
meal gap suggestions
low-stock signals
expired replacement signals
common pantry/staple signals
user-provided shopping intent
```

## Important boundary

This stage should still avoid creating persistent shopping-list records unless the user explicitly asks for that behaviour and a separate write tool has been designed and tested.

Possible output groups:

```text
essential restocks
meal-supporting items
optional improvements
expired replacements
low-priority pantry items
```

---

# Future Shopping List Support

Possible future files:

```text
user_shopping_list.csv
user_shopping_list_items.csv
```

Possible future write tools:

```text
create_shopping_list
add_shopping_list_item
update_shopping_list_item
remove_shopping_list_item
confirm_shopping_list_draft
```

Design questions:

```text
Should generated shopping items require confirmation?
Should low-stock inventory automatically become shopping-list entries?
How should priority be represented?
How should repeated staples be handled?
Should shopping-list items link back to meal opportunities?
Should shopping-list items link back to source inventory signals?
```

Recommendation:

```text
Start with draft-only shopping lists before adding persistent shopping-list writes.
```

---

# Version 1.6 — User Feedback and Learning Over Time

## Goal

Begin recording feedback about recommendation usefulness.

This should come before any machine-learning recommender.

Possible future files:

```text
user_recommendation_events.csv
user_recommendation_feedback.csv
```

Possible event fields:

```text
recommendation_id
recommendation_type
created_at
signals_used
suggested_items
suggested_meals
confidence
priority
accepted
rejected
ignored
modified
user_note
```

Possible feedback signals:

```text
user cooked suggested meal
user bought suggested item
user rejected suggestion
user substituted ingredient
user repeatedly ignores similar suggestions
item frequently wasted after purchase
```

Important principle:

```text
Do not build a train/test recommender until enough labelled recommendation feedback exists.
```

---

# Version 1.7 — Nutrition-Aware Opportunities

## Goal

Introduce soft nutrition opportunities after the meal and restock layers are stable.

Possible signals:

```text
protein opportunity
fibre opportunity
vegetable opportunity
balanced meal opportunity
higher-energy meal option
lighter meal option
```

Boundary:

```text
Nutrition suggestions should be optional, gentle, and non-medical.
```

The assistant should not present itself as a dietitian or medical advisor.

---

# Version 1.8 — Cost, Waste, and Convenience Ranking

## Goal

Improve ranking using practical household constraints.

Possible ranking factors:

```text
use-soon priority
number of available ingredients
number of missing ingredients
waste reduction
cost efficiency
user enjoyment
estimated effort
leftover potential
nutrition value
```

Important idea:

```text
The best recommendation is not always the cheapest, healthiest, or most complete.
It should balance usefulness, confidence, user preference, and current grocery context.
```

---

# Future Meal Templates and Learning

Possible future files:

```text
user_meal_templates.csv
user_meal_template_items.csv
user_meal_aliases.csv
```

Possible tools:

```text
create_meal_template
add_meal_alias
suggest_meal_template_from_history
log_meal_from_template
```

Safety rule:

```text
A known meal template can help create intake records, but inventory deduction should still require explicit user intent.
```

---

# Future Consumption Adjustment and Reversal

Possible tools:

```text
adjust_inventory_consumption_event
reverse_inventory_consumption_event
restore_inventory_from_consumption_event
```

Purpose:

```text
Correct accidental inventory deductions or logging mistakes.
```

This becomes more important as the assistant starts helping users act on suggestions.

---

# Future Recipe and Batch Cooking Support

Possible future concepts:

```text
recipe templates
batch meal templates
servings planned
servings eaten
servings stored
leftover tracking
```

Boundary:

```text
Recipe support should not be required for basic meal opportunities.
Simple meal opportunities can stay template-based until the project needs deeper recipe structure.
```

---

# Future MCP Agent Behaviour

Future agents should use planning tools to gather structured evidence before presenting advice.

Expected flow:

```text
user asks for food advice
↓
agent calls relevant planning/recommendation tool
↓
agent explains draft suggestions with confidence and caveats
↓
user confirms an action
↓
agent calls explicit write tool if needed
```

Planning and suggestion tools should not silently perform writes.


## Future Direction: Camera-Assisted Inventory Input

Camera-assisted inventory input is a future workflow where users can capture
product packages, nutrition labels, receipts, or pantry/fridge photos to reduce
manual grocery entry.

The system should not write image-derived information directly into confirmed
inventory. Instead, image-derived data should enter a staging layer where OCR,
vision extraction, confidence scoring, validation warnings, and user confirmation
occur before any inventory, product catalog, nutrition, or purchase-history CSVs
are updated.

Initial implementation should begin with text-first tools such as
`stage_receipt_text` and `stage_nutrition_label_text`, allowing the project to
simulate OCR output before adding real image upload or camera integrations.

## Future Directio: Voice-Assisted Inventory Input

Your voice
↓
audio recording
↓
speech-to-text transcript
↓
agent interprets intent
↓
MCP tool/resource/prompt selection
↓
confirmation for write actions
↓
inventory / intake / meal planning update