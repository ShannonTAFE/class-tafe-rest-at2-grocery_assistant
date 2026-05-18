# MCP Grocery Assistant — Learning Concept

## Purpose

This document explains how the Grocery Assistant MCP server can support agent learning over time.

The goal is not to make the agent permanently improve itself internally. Instead, the goal is to let agents read and write structured user context through explicit, testable MCP tools and resources.

In this project, learning means storing useful user food context as durable project data.

Examples include:

- meal aliases
- usual meal names
- common ingredients
- meal templates
- user behaviour patterns
- inventory relationships
- preferred logging behaviour
- safe inventory deduction rules

This learning layer should help future agents interpret user requests more accurately while keeping important actions, especially inventory mutation, explicit and controlled.

---

## Core Principle

The Grocery Assistant MCP server enables agent learning by storing explicit, reviewable user context as structured data.

Agents may use this context to interpret future requests, but durable learning lives in the server data, not in the agent itself.

A simple way to describe this is:

```text
Agent = reasoning layer
MCP server = memory and action layer
Project data = durable learned context
```

The agent may be clever during a conversation, but the server should hold the reliable long-term knowledge.

---

## Why This Matters

An agent may have limited ability to permanently improve itself or remember every user preference across sessions. Even when memory exists, it may not be inspectable, portable, or testable in the same way as project data.

The MCP server can solve this by storing learned context in explicit files such as CSVs.

This makes the assistant:

- more reliable
- easier to test
- easier to debug
- easier to explain
- safer around inventory-changing actions
- less dependent on one specific model or chat session

Instead of relying on hidden model memory, the project can store facts like:

```text
"spag bog" means "Spaghetti bolognese"
```

or:

```text
The user's usual spaghetti bolognese contains spaghetti, beef mince, tomato sauce, onion, garlic, and parmesan.
```

This means future agents can retrieve that context and behave consistently.

---

## Learning Does Not Mean Silent Automation

Learning should improve interpretation, not silently trigger risky actions.

For this project, a key safety rule is:

```text
Meal recognition and inventory consumption are separate decisions.
```

A known meal name can be expanded into intake items, but inventory should only be deducted through explicit inventory-linked workflows.

For example:

```text
User: I ate spag bog.
```

Safe learned interpretation:

```text
spag bog = Spaghetti bolognese
```

Potential safe action:

```text
Log a meal called Spaghetti bolognese.
```

Potential safe future action:

```text
Use a saved meal template to create child intake items.
```

Unsafe automatic action:

```text
Deduct pasta, beef mince, tomato sauce, and parmesan from inventory without confirmation.
```

The system should not assume that a meal name means current inventory was consumed.

---

## Example: "Spag Bog"

The phrase:

```text
I ate spag bog.
```

could mean several different things:

1. The user ate a meal called spaghetti bolognese.
2. The user ate their usual spaghetti bolognese meal.
3. The user ate a meal that can be broken into child intake items.
4. The user cooked the meal using ingredients from current inventory.
5. The user ate leftovers from a previous batch.
6. The user ate takeaway or someone else's cooking.

These meanings should not be collapsed into one action.

The project should handle them in layers.

---

## Learning Layer 1 — Meal Aliases

The first type of learning is meal name recognition.

The system can learn that casual user phrases map to canonical meal names.

Example:

```text
spag bog → Spaghetti bolognese
spaghetti bog → Spaghetti bolognese
bolognese → Spaghetti bolognese
```

A future file could be:

```text
user_meal_aliases.csv
```

Possible fields:

```text
alias_id
alias
canonical_meal_name
confidence
usage_count
last_used_date
active
notes
```

Example row:

```csv
alias_id,alias,canonical_meal_name,confidence,usage_count,last_used_date,active,notes
alias_001,spag bog,Spaghetti bolognese,high,7,2026-05-18,true,User commonly uses this phrase
```

This allows future agents to understand what the user means without changing inventory or making unsafe assumptions.

---

## Learning Layer 2 — Meal Templates

The next type of learning is meal structure.

The system can learn that a user's usual meal often contains a known set of child items.

Example:

```text
Spaghetti bolognese usually includes:
- spaghetti
- beef mince
- tomato sauce
- onion
- garlic
- parmesan
```

A future file could be:

```text
user_meal_templates.csv
```

Possible fields:

```text
template_id
meal_name
default_meal_type
default_source
template_confidence
inventory_policy
active
notes
```

Example row:

```csv
template_id,meal_name,default_meal_type,default_source,template_confidence,inventory_policy,active,notes
meal_tpl_001,Spaghetti bolognese,dinner,home,medium,intake_only,true,User's usual home version
```

The important field is:

```text
inventory_policy
```

Recommended values:

```text
intake_only
ask_before_deducting
inventory_linked
```

The default should be:

```text
intake_only
```

This prevents learned meal templates from silently becoming inventory deduction workflows.

---

## Learning Layer 3 — Meal Template Items

Meal template items describe the usual components of a learned meal.

A future file could be:

```text
user_meal_template_items.csv
```

Possible fields:

```text
template_item_id
template_id
food_item
category
default_quantity_used
unit
default_servings_used
optional
stock_id_hint
notes
```

Example rows:

```csv
template_item_id,template_id,food_item,category,default_quantity_used,unit,default_servings_used,optional,stock_id_hint,notes
tpl_item_001,meal_tpl_001,spaghetti,pantry,100,g,0,false,,Usually pasta base
tpl_item_002,meal_tpl_001,beef mince,protein,125,g,0,false,,Main protein
tpl_item_003,meal_tpl_001,tomato sauce,pantry,150,g,0,false,,Sauce
tpl_item_004,meal_tpl_001,parmesan,dairy,10,g,0,true,,Optional topping
```

The field `stock_id_hint` should be treated carefully.

It may suggest a likely inventory relationship, but it should not automatically cause inventory deduction.

---

## Learning Layer 4 — Learning Events

Learning should be auditable.

The system should be able to show what was learned, when it was learned, and why.

A future file could be:

```text
user_learning_events.csv
```

Possible fields:

```text
learning_event_id
date
event_type
target_type
target_id
evidence
created_by
confidence
notes
```

Example rows:

```csv
learning_event_id,date,event_type,target_type,target_id,evidence,created_by,confidence,notes
learn_001,2026-05-18,alias_created,meal_alias,alias_001,"User said spag bog means spaghetti bolognese",agent,high,
learn_002,2026-05-18,template_suggested,meal_template,meal_tpl_001,"Spag bog was logged multiple times with similar child items",agent,medium,Needs user confirmation
```

This gives the project a clear history of how learned context entered the system.

---

## Recommended MCP Learning Tools

The learning layer should be exposed through explicit MCP tools.

### Read and Search Tools

Possible tools:

```text
search_meal_aliases
search_meal_templates
get_meal_template
suggest_meal_templates_from_history
```

These allow the agent to inspect learned context before deciding what to do.

### Write Tools

Possible tools:

```text
create_meal_alias
update_meal_alias
deactivate_meal_alias

create_meal_template
update_meal_template
deactivate_meal_template

add_meal_template_item
update_meal_template_item
remove_meal_template_item

record_learning_event
```

These allow agents to create or update durable learned context.

The tools should validate data, create backups, and return structured results just like the rest of the project.

---

## Example Agent Workflows

### Workflow 1 — User Teaches an Alias

User says:

```text
When I say spag bog, I mean spaghetti bolognese.
```

Agent action:

```text
create_meal_alias
record_learning_event
```

Stored result:

```text
alias: spag bog
canonical_meal_name: Spaghetti bolognese
confidence: high
```

Future result:

```text
When the user says "spag bog", the agent can recognise the canonical meal name.
```

---

### Workflow 2 — User Teaches a Meal Template

User says:

```text
My usual spag bog has pasta, beef mince, tomato sauce, onion, garlic, and parmesan.
```

Agent action:

```text
create_meal_template
add_meal_template_item for each component
record_learning_event
```

Stored result:

```text
Spaghetti bolognese template with multiple child items.
```

Default policy:

```text
inventory_policy = intake_only
```

Future result:

```text
The agent can create parent and child intake rows from the template, without deducting inventory.
```

---

### Workflow 3 — User Logs a Known Meal

User says:

```text
I ate spag bog.
```

Agent checks:

```text
Is there an alias for spag bog?
Is there a meal template for the canonical meal?
What is the inventory policy?
```

If alias exists but no template exists:

```text
Log parent meal only.
```

If alias and intake-only template exist:

```text
Use add_meal_with_items to create parent and child intake rows.
Do not deduct inventory.
```

If inventory-linked template exists but user did not ask to deduct inventory:

```text
Prefer intake-only logging or ask before deducting.
```

---

### Workflow 4 — User Explicitly Requests Inventory Deduction

User says:

```text
Log my usual spag bog and update inventory.
```

Agent checks:

```text
Is there an inventory-linked template?
Are stock items available?
Are quantities known?
Is the workflow supported by the current version?
```

Future action:

```text
Use an inventory-linked batch meal tool.
```

This should not be handled by ordinary intake-only batch logging.

---

### Workflow 5 — User Logs Leftovers

User says:

```text
I had leftover spag bog.
```

Agent action:

```text
Log intake.
Do not deduct raw ingredients.
```

Reason:

```text
The ingredients may already have been deducted when the original batch was cooked.
```

This protects the system from double-counting inventory consumption.

---

## Important Boundaries

The learning layer should not blur these project concepts:

```text
Intake = what the user ate
Inventory = what the user currently has
Consumption = inventory being used or deducted
Waste = food being discarded
Templates = reusable knowledge about usual meals
Aliases = user-specific language shortcuts
```

A meal can be recognised without being deducted from inventory.

A meal can be expanded into child items without being deducted from inventory.

Inventory should only change through explicit inventory-linked tools.

---

## Relationship to Version 1.4B

Version 1.4B should stay focused on batch meal logging.

Primary goal:

```text
add_meal_with_items
```

This should:

```text
create one parent intake entry
create multiple child intake item rows
validate everything before writing
save related intake CSVs safely
return the created parent and children
```

It should not:

```text
deduct inventory
create inventory consumption records
create food waste records
auto-learn meal templates
auto-save aliases
```

However, Version 1.4B prepares the project for future learning because it gives the system a clean structure for parent and child meal records.

Later, learned templates can call the same batch logging workflow.

---

## Future Version Direction

A possible staged roadmap:

```text
Version 1.4B:
    Batch parent-and-child intake logging.
    No learning yet.
    No inventory mutation.

Version 1.5:
    Meal aliases and meal templates.
    Basic create/search/update/deactivate tools.

Version 1.6:
    Learning suggestions from repeated intake history.
    Agent can suggest aliases/templates, but user approval is preferred.

Version 1.7:
    Template-based meal logging.
    "I ate my usual spag bog" can expand into child intake items.

Version 1.8 or later:
    Inventory-linked meal templates.
    Explicit inventory deduction workflows.
    Strong validation and confirmation rules.
```

This roadmap keeps the project safe and understandable as it becomes more personalised.

---

## Recommended Design Rule for Documentation

Use this as a project rule:

```text
The Grocery Assistant MCP server enables learning by storing explicit, reviewable user food context as structured data.

Learned aliases and templates may help agents interpret future meal requests, but they must not silently mutate inventory.

Inventory mutation remains limited to explicit consumption workflows.
```

---

## Summary

The project should help agents learn by giving them durable, structured context to read and write.

The learning layer should store what the user means, what meals usually contain, and how the user tends to log food.

However, learned context should not automatically trigger stock-changing actions.

The safest long-term design is:

```text
Learn meanings.
Learn patterns.
Suggest reusable templates.
Require explicit workflows for inventory mutation.
```

This allows the Grocery Assistant to become more personalised while keeping the data model clear, testable, and safe.

