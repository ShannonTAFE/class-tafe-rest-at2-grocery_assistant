# Grocery Assistant MCP Roadmap

## Purpose

This roadmap documents the planned progression of the Grocery Assistant MCP project from a read-only MCP server into a safe write-capable assistant and eventually a more intelligent grocery planning system.

The project is built around four core areas:

```text
Inventory = what the user has, had, or wants to remember for planning
Intake = what the user ate
Inventory consumption = why tracked inventory quantities changed
Waste = food that was discarded, spoiled, expired, unused, or otherwise wasted
```

Main principle:

```text
Build safe, explicit write foundations before adding automation.
```

---

# Version Timeline

```text
Version 1.0 — Read-only MCP grocery assistant
Version 1.1 — Safe write tools for inventory, intake, and waste
Version 1.2 — Relationship-safe intake search, editing, and cleanup
Version 1.3 — Controlled inventory consumption tools and consumption event logging
Version 1.4 — Batch meal logging and transaction-like workflows
Version 1.5 — Planning intelligence and suggestion workflows
```

---

# Version 1.0 — Read-Only MCP Grocery Assistant

Goal:

```text
Expose grocery data safely as read-only MCP resources and summary tools.
```

Completed capabilities:

- read inventory
- read intake history
- read intake items
- search inventory
- review recent intake
- summarise daily intake
- expose prompts for common assistant workflows
- test resources and tools with MCP Inspector and curl

---

# Version 1.1 — Safe Write Foundation

Goal:

```text
Add controlled write tools without hidden side effects.
```

Completed capabilities:

- add inventory items
- update inventory items
- remove inventory items
- add parent intake entries
- add child intake items
- food waste handling through explicit removal workflows

Key decisions:

- Intake logging does not automatically reduce inventory.
- Intake items must link to a valid parent intake entry.
- Intake item `stock_id` is optional.
- Waste records are created only when removal type is waste-related.
- MCP tool wrappers remain thin.
- Business logic stays in the service layer.

---

# Version 1.2 — Intake Relationship Editing and Cleanup

Goal:

```text
Safely search, update, and remove parent/child intake records.
```

Completed capabilities:

- search intake parent entries and child items
- update parent intake entries
- update child intake items
- remove child intake items
- block parent removal while child items exist
- avoid cascade deletion

---

# Version 1.3 — Controlled Inventory Consumption

Goal:

```text
Allow explicit inventory deduction while preserving an event history.
```

Completed capabilities:

- consume inventory without creating intake rows
- create intake items from inventory
- reduce quantity and/or servings
- record inventory consumption events
- link consumption events to intake items
- expose inventory consumption as a resource

Key decision:

```text
Ordinary intake logging still does not silently deduct inventory.
```

---

# Version 1.4 — Batch Meal Logging and Transaction-Like Workflows

Status:

```text
Current closeout baseline.
```

Goal:

```text
Create safe batch workflows that coordinate parent meals, child items, and optionally inventory consumption.
```

Completed stages:

```text
Version 1.4A — Core service refactor
Version 1.4B — Intake-only batch meal logging
Version 1.4C — Inventory-linked batch meal logging
```

Completed tools:

```text
add_meal_with_items
add_meal_with_inventory_items
```

Version 1.4B rule:

```text
Create parent and child intake records without inventory deduction.
```

Version 1.4C rule:

```text
Deduct inventory only when the request explicitly uses inventory-linked items.
```

Non-goals:

- no automatic meal alias learning
- no recipe system
- no shopping list generation
- no automatic inventory deduction from a meal name alone
- no hidden food waste creation during normal meal logging

---

# Version 1.5 — Planning Intelligence

Goal:

```text
Add read-heavy planning and suggestion tools that help the assistant reason from inventory,
intake, consumption, and waste records without silently mutating records.
```

Completed stages:

```text
Version 1.5A — Planning signal foundation
Version 1.5B — Focused inventory planning reviews
Version 1.5C — Signal-based meal suggestion drafts
Version 1.5D — Restock/shopping-list draft suggestions informed by meal gaps
```

Next recommended refinement:

```text
Version 1.5E — Recommendation quality refinement
```

Safety principle:

```text
Suggestions can be intelligent, but writes must remain explicit.
```

Inventory-changing, intake-changing, waste-changing, and shopping-list-changing actions should continue to route through tested write tools.

---

## Version 1.5A — Planning Signal Foundation

Completed capability:

```text
review_planning_context
```

Purpose:

```text
Give the agent a structured planning overview before it suggests meals, restocks,
shopping-list drafts, or next actions.
```

The planning context may include:

```text
inventory signals
recent intake context
data-quality signals
warnings
safe next actions
read-only safety metadata
records checked metadata
```

Key design decision:

```text
Planning signals are derived from source records. Source CSV files should remain clean
and should not be overloaded as feature tables.
```

---

## Version 1.5B — Focused Inventory Planning Reviews

Completed focused tools:

```text
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
```

Purpose:

```text
Let the agent inspect focused subsets of the planning signal layer without manually
reading the entire planning context every time.
```

These tools are review tools, not recommendation or write tools.

They should:

```text
reuse the planning context layer
filter relevant signal groups
return stable planning responses
preserve read-only safety metadata
include warnings and next-action guidance
```

They should not:

```text
update inventory
create shopping-list records
deduct inventory
log intake
create waste records
infer corrections automatically
```

---

## Version 1.5C — Signal-Based Meal Suggestion Drafts

Completed capability:

```text
draft_meal_suggestions
```

Purpose:

```text
Draft basic meal opportunities from inventory signals, food role inference,
simple meal templates, use-soon priority, and gap-tolerant matching.
```

Important design decision:

```text
Meal suggestions came before restock suggestions because restocking becomes more useful
when it is linked to meals the user might actually eat.
```

The tool should produce explainable meal opportunity drafts, not full recipes.

It may return:

```text
meal_name
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

Boundary:

```text
draft_meal_suggestions does not log meals, deduct inventory, create recipes,
optimise nutrition, or write shopping-list records.
```

---

## Version 1.5D — Restock and Shopping-List Draft Suggestions

Completed capability:

```text
draft_restock_suggestions
```

Goal:

```text
Draft restock suggestions from inventory urgency and meal-opportunity gaps.
```

Version 1.5D avoids a simple stock-only checklist.

Less useful:

```text
rice is low → buy rice
```

More useful:

```text
rice is low and supports several suggested meals
```

Source signals:

```text
low-stock inventory signals
out-of-stock inventory signals
expired replacement signals
meal gap signals from draft_meal_suggestions
generic role-gap signals
usefulness across multiple meal opportunities
```

The tool may return:

```text
item_name
candidate_type
suggestion_type
priority
confidence
current_status
source_stock_ids
role
supports_meals
reasons
suggested_action
would_create_shopping_list_record
requires_user_confirmation_before_write
```

Key design decision:

```text
Version 1.5D creates shopping-list-shaped suggestions, not persistent shopping-list rows.
```

Boundary:

```text
draft_restock_suggestions does not create shopping-list records, update inventory,
deduct stock, log intake, or create waste records.
```

Future shopping-list persistence should be handled by a separate explicit write workflow after user confirmation.

---

## Recommended Next Direction

The next useful Version 1.5 refinement is:

```text
Version 1.5E — Recommendation quality refinement
```

Possible focus areas:

```text
improve food role inference
improve meal-template coverage
improve restock priority scoring
improve confidence scoring
improve generic role-gap explanations
improve tolerance of incomplete CSV data
```

A later major version can introduce:

```text
Version 1.6 — Confirmed shopping-list workflow
```

That should be the point where persistent shopping-list records and shopping-list write tools are designed.

---

## Agent and MCP Grocery Server Relationship

Version 1.5 introduces planning intelligence, but it does not change the core responsibility split between the LLM agent and the MCP grocery server.

The connected LLM agent is responsible for interpreting the user request, deciding which MCP tools or resources are useful, and communicating a helpful response to the user.

The MCP grocery server is responsible for exposing safe, structured, project-aware data and actions.

The relationship can be understood as:

```text
Raw grocery CSV data
   ↓
MCP resources and service-layer functions
   ↓
Version 1.5 planning tools
   ↓
Structured planning signals and draft suggestions
   ↓
LLM agent reasoning and communication
   ↓
User confirmation
   ↓
Existing safe write tools, when needed
```

Planning tools do not replace the agent's reasoning. They prepare reliable evidence that makes the agent's reasoning safer, more consistent, and easier to test.

---

## Why Planning Tools Are Still Useful When the Agent Can Reason

### Consistency

Planning rules can be defined once in the service layer instead of being reinterpreted differently in every conversation.

Example:

```text
expired items should not be suggested as usable meal ingredients
```

### Safety

Planning tools can make safety boundaries explicit.

Example:

```json
{
  "requires_user_confirmation_before_write": true,
  "inventory_mutation_performed": false
}
```

### Reduced Context Load

As inventory, intake, consumption, and waste records grow, the agent should not inspect every row manually for every planning question.

Planning tools condense raw records into useful signals.

### Testability

Service-layer planning functions can be tested.

Tests can verify that:

```text
expired items are excluded from usable meal ingredients
draft shopping-list tools do not write to CSV files
low-stock items are ranked consistently
planning tools do not mutate inventory, intake, waste, or consumption records
```

### Project-Specific Intelligence

The grocery assistant has rules that a general LLM may not infer reliably.

Example:

```text
Out-of-stock inventory items are still useful records.
They may represent staples, repeated purchases, or future restock candidates.
```

Planning tools preserve these meanings in a structured format.

---

## Version 1.5 Design Rule

Every Version 1.5 planning tool should answer:

```text
What does the agent need to know before giving advice?
```

It should not answer:

```text
What should the system automatically change?
```

Version 1.5 is a suggestion and decision-support layer, not an automation layer.

Version 1.5 tools may suggest, rank, explain, and draft.

They should not silently mutate:

```text
inventory records
intake records
inventory consumption records
waste records
shopping list records
```

Any mutation should continue to route through explicit, tested write tools.
