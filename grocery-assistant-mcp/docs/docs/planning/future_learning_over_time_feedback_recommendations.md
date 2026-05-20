# Future Learning Over Time and Feedback-Aware Recommendations

**Updated:** 2026-05-19  
**Status:** Future roadmap concept aligned with Version 1.5A signal foundation  
**Implementation mode:** Planning and architecture only; no code in this document

---

## Purpose

This document records an important future direction for the Grocery Assistant MCP project: learning from user behaviour over time.

The project should eventually become more personalised, but it should not start with a machine-learning recommender.

The right sequence is:

```text
1. Collect clean source records.
2. Derive planning signals.
3. Use signals for explainable suggestions.
4. Record recommendation events and user feedback.
5. Learn patterns over time.
6. Consider machine learning only when enough labelled feedback exists.
```

Version 1.5A supports this future by creating the signal foundation.

---

## Current Position

The current grocery CSV files should be treated as source-of-truth records.

They are not yet machine-learning feature tables.

Core records include:

```text
inventory
intake
intake items
inventory consumption
waste
```

These records describe:

```text
what exists
what was eaten
what was used
what was wasted
what changed over time
```

From these records, the planning layer can derive signals such as:

```text
use-soon items
low-stock items
out-of-stock items
expired items
recently eaten meals
data-quality warnings
safe next actions
```

This is enough to make the agent more useful before any machine learning exists.

---

## Why Not Build a Train/Test Recommender Yet?

A machine-learning recommendation pipeline would currently be premature.

The project does not yet have enough of the most important ingredient:

```text
labelled recommendation feedback
```

A future model would need examples like:

```text
recommendation shown
signals used
user accepted it
user rejected it
user ignored it
user modified it
user rated it highly
user cooked it later
user bought the suggested item later
```

Without this, a train/test pipeline risks training on weak or artificial labels.

Version 1.5 should therefore focus first on:

```text
interpretable signals
safe planning responses
structured recommendation events later
feedback collection later
```

---

## Stage 1 — Signal-Based Recommendations

This is the recommended Version 1.5 direction.

The system uses:

```text
rules
heuristics
derived planning features
structured signals
LLM reasoning
```

Example flow:

```text
Inventory record:
Spinach, in_stock, expires soon

Derived feature:
days until expiry is low

Signal:
use_soon

Agent guidance:
Prioritise spinach in meal suggestions if the user wants to reduce waste.

Possible user-facing suggestion:
A spinach omelette could be a good option because it uses spinach before it expires.
```

Benefits:

```text
interpretable
testable
safe
works with small datasets
works with imperfect user input
easy to explain to the user
```

This should come before feedback-aware or ML-assisted recommendations.

---

## Stage 2 — Feedback-Aware Recommendations

After basic suggestions exist, the project can record what was suggested and how the user responded.

Possible future files:

```text
user_recommendation_events.csv
user_recommendation_feedback.csv
user_meal_preferences.csv
```

## Recommendation Event Fields

A future recommendation event could store:

```text
recommendation_id
date
time
recommendation_type
suggested_item_or_meal
signals_used
agent_confidence
reason_summary
source_tool
shown_to_user
notes
```

## Recommendation Feedback Fields

A future feedback file could store:

```text
feedback_id
recommendation_id
date
user_action
accepted
rejected
ignored
modified
rated_enjoyment
rated_effort
rated_cost
would_repeat
notes
```

## What This Enables

With feedback, the assistant can learn simple patterns such as:

```text
The user often accepts rice bowl suggestions.
The user often rejects tuna-based meals.
The user prefers low-effort weekday dinners.
The user values meals that use existing inventory.
The user prefers cheap suggestions near the end of the week.
The user dislikes repeating the same dinner too often.
```

At this stage, the system still does not need a machine-learning model.

It can use transparent rules such as:

```text
Recommend accepted meal types more often.
Avoid repeatedly rejected ingredients.
Prioritise low-effort meals when the user often chooses them.
Prefer meals that match previously accepted substitutions.
Do not infer a strong dislike from one rejection.
```

---

## Stage 3 — ML-Assisted Personalization

Machine learning may become useful only after enough feedback has been collected.

Possible future model tasks:

```text
predict whether the user will accept a meal suggestion
rank candidate meals by likely preference
predict restock priority
predict waste risk
predict likely missing staples
predict preferred substitutions
```

Possible labels:

```text
accepted recommendation
rejected recommendation
meal logged after suggestion
high enjoyment rating
low effort rating
item purchased after suggestion
waste reduced after suggestion
```

Possible input features:

```text
recommendation type
signals used
inventory context
recent intake context
day of week
meal type
effort estimate
cost estimate
use-soon ingredients
past acceptance patterns
past rejection patterns
```

This should only be considered when the project has:

```text
enough historical recommendation examples
clear labels
reliable feedback records
enough variety in suggestions and user responses
clear evaluation metrics
```

---

## Important Architecture Principle

Do not mix future recommendation features directly into the source CSV files.

Better structure:

```text
Source CSV records
   ↓
Read service
   ↓
Derived planning features
   ↓
Planning signals
   ↓
Recommendation candidates
   ↓
Recommendation events
   ↓
User feedback
   ↓
Future learning layer
```

This keeps each layer understandable.

---

## Future Feedback Loop

A future feedback loop could work like this:

```text
1. Planning layer identifies use-soon spinach and available eggs.
2. Assistant suggests spinach omelette.
3. Recommendation event is logged.
4. User accepts, rejects, ignores, or modifies the suggestion.
5. Feedback is logged.
6. Future suggestions consider this feedback.
```

The important idea is that the system learns from recommendation outcomes, not just from raw inventory and intake.

---

## Early Signals That Support Future Learning

Version 1.5A should collect or derive strong foundation signals early.

Most useful early signals:

```text
available_inventory
low_stock
very_low_stock
out_of_stock
expired
use_soon
no_expiry_data
missing_quantity
missing_unit
missing_stock_status
recently_eaten
no_recent_intake_records
write_requires_confirmation
recommendations_are_not_actions
```

These are useful now and can later become features for recommendation ranking.

---

## Future Learning Signal Ideas

Future versions may support:

```text
accepted_meal_pattern
rejected_ingredient_pattern
preferred_meal_type
preferred_effort_level
preferred_cost_level
repeat_meal_tolerance
staple_item_pattern
frequent_waste_item
fast_consumption_item
slow_consumption_item
substitution_preference
```

These should be treated carefully.

A pattern should not become a strong preference too quickly.

Example caution:

```text
The user eating oats five times may mean they like oats.
It may also mean oats were cheap, convenient, or the only breakfast available.
```

Future learning should therefore use confidence and avoid overclaiming.

---

## Safety Boundary

Future learning should never silently mutate records or make strong claims about the user without evidence.

The system should avoid statements like:

```text
You love tuna.
You always want low-carb meals.
You should stop buying bread.
```

Safer statements:

```text
You have accepted rice bowl suggestions several times, so I can prioritise similar ideas.
You have rejected tuna suggestions before, so I will avoid making tuna the main option unless you ask.
Bread has appeared in waste records more than once, so it may be worth buying smaller amounts.
```

The assistant should remain transparent, adjustable, and user-controlled.

---

## Relationship to Version 1.5A

Version 1.5A does not need to implement feedback-aware learning.

However, it should prepare for it by making signals structured and referenceable.

The key preparation is:

```text
Every future recommendation should be able to reference the signals that supported it.
```

For example:

```text
recommendation: spinach omelette
supporting signals: use_soon spinach, available eggs, recent dinner variety gap
```

This is what allows future recommendation events to become meaningful training or feedback data.

---

## Recommended Future Roadmap

```text
Version 1.5A — Planning signal foundation
Version 1.5B — Low-stock, use-soon, and restock review tools
Version 1.5C — Basic meal suggestion from inventory
Version 1.5D — Recommendation event and feedback logging
Version 1.5E — Feedback-aware ranking and preference-sensitive suggestions
Version 1.6+ — Optional ML-assisted personalization if enough feedback data exists
```

---

## Summary

The project should learn over time, but learning should be built gradually.

The recommended path is:

```text
Do not start with machine learning.
Start with clean source records.
Build structured planning signals.
Use those signals for explainable suggestions.
Record recommendation events only once suggestions are stable.
Collect feedback in a dedicated feedback layer.
Use rules before ML.
Only consider ML once there is enough labelled feedback.
```

This gives the Grocery Assistant MCP project a safer and more realistic path toward personalised recommendations.
