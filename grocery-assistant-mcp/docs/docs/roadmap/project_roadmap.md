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

Possible goals:

- meal suggestions from available inventory
- restock suggestions
- low-stock review
- food waste pattern review
- simple shopping list draft support
- meal planning prompts based on inventory and recent intake

Safety principle:

```text
Suggestions can be intelligent, but writes should remain explicit.
```

Inventory-changing actions should still route through tested tools.

## Agent and MCP Grocery Server Relationship

Version 1.5 introduces planning intelligence, but it does not change the core responsibility split between the LLM agent and the MCP grocery server.

The connected LLM agent is responsible for interpreting the user request, deciding which MCP tools or resources are useful, and communicating a helpful response to the user.

The MCP grocery server is responsible for exposing safe, structured, project-aware data and actions.

In this project, planning tools should not be viewed as replacing the agent's reasoning. Instead, they provide the agent with reliable planning signals that make its reasoning safer, more consistent, and easier to test.

The relationship can be understood as:

```text
Raw grocery CSV data
   ↓
MCP resources and service-layer functions
   ↓
Version 1.5 planning tools
   ↓
Structured planning signals
   ↓
LLM agent reasoning and communication
   ↓
User confirmation
   ↓
Existing safe write tools, when needed
```

The agent may be able to suggest meals, restocks, or shopping ideas by reading raw resources directly. However, relying on the agent to manually interpret all grocery records every time would make behaviour less consistent and harder to test.

Version 1.5 planning tools exist to prepare the ground for the agent.

They help answer questions such as:

```text
Which inventory items are available?
Which items are low, very low, out of stock, or expired?
Which items should be used soon?
Which recent meals should be avoided to reduce repetition?
Which restock suggestions are high priority?
Which meal suggestions are grounded in actual inventory?
Which actions would require explicit user confirmation?
```

The tool prepares structured evidence.

The agent turns that evidence into a useful conversation.

For example, a meal suggestion tool may return:

```json
{
  "meal_suggestions": [
    {
      "meal_name": "Chicken rice bowl",
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
      "reason": "Uses available protein and pantry stock.",
      "confidence": "high",
      "safe_to_log_with_inventory_items": true,
      "requires_user_confirmation_before_write": true
    }
  ]
}
```

The LLM agent can then explain the recommendation naturally:

```text
A good option tonight is a chicken rice bowl. It uses chicken and rice from your inventory. Sauce or fresh greens would improve it, but they are optional.
```

If the user then asks to log the meal, the agent should route the action through an existing safe write workflow such as:

```text
add_meal_with_items
add_meal_with_inventory_items
```

Version 1.5 planning tools should not directly create intake records, deduct inventory, create waste records, or persist shopping list records unless that behaviour has been explicitly designed, tested, and confirmed by the user.

The core responsibility split is:

```text
Planning tools = prepare safe, structured evidence
LLM agent = interpret, reason, and communicate
Write tools = mutate records only after explicit user intent
```

This keeps Version 1.5 aligned with the existing project principle:

```text
Build safe, explicit write foundations before adding automation.
```

## Why Planning Tools Are Still Useful When the Agent Can Reason

The LLM agent is capable of reasoning over grocery data, but project-specific tools provide several advantages.

### Consistency

Planning rules can be defined once in the service layer instead of being reinterpreted differently in each conversation.

For example:

```text
low, very_low, out, and expired are inventory attention states.
```

Once this rule is implemented in a planning function, every connected agent receives the same interpretation.

### Safety

Planning tools can make safety boundaries explicit in their outputs.

For example:

```json
{
  "requires_user_confirmation_before_write": true,
  "inventory_mutation_performed": false
}
```

This helps prevent the agent from accidentally treating a suggestion as an action.

### Reduced Context Load

As inventory, intake, consumption, and waste records grow, the agent should not need to inspect every row manually for every planning question.

A planning tool can condense raw records into useful signals such as:

```text
Top use-soon ingredients
Low-stock staples
Out-of-stock restock candidates
Recent meals to avoid repeating
Candidate ingredients for meal suggestions
```

### Testability

The behaviour of service-layer planning functions can be tested.

For example, tests can verify that:

```text
Expired items are not suggested as usable ingredients.
Draft shopping list tools do not write to CSV files.
Low-stock items are ranked consistently.
Recent intake is considered when suggesting the next meal.
Planning tools do not mutate inventory, intake, waste, or consumption records.
```

The agent's final wording may vary, but the tool output can remain predictable and testable.

### Project-Specific Intelligence

The grocery assistant has rules and meanings that a general LLM may not infer reliably.

For example:

```text
Out-of-stock inventory items are still useful records.
They may represent staples, repeated purchases, or future restock candidates.
```

Planning tools can preserve these project-specific meanings and provide them to the agent in a structured format.

## Version 1.5 Design Rule

Every Version 1.5 planning tool should answer this question:

```text
What does the agent need to know before giving advice?
```

It should not answer:

```text
What should the system automatically change?
```

Version 1.5 is therefore a suggestion and decision-support layer, not an automation layer.

Suggested planning tools may include:

```text
review_low_stock_items
suggest_restock_items
suggest_meals_from_inventory
suggest_next_meal
review_recent_intake_patterns
draft_shopping_list
```

These tools may suggest, rank, explain, and draft.

They should not silently mutate:

```text
inventory records
intake records
inventory consumption records
waste records
shopping list records
```

Any mutation should continue to route through explicit, tested write tools.
