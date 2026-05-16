# Grocery Assistant MCP Roadmap

## Purpose

This roadmap documents the planned progression of the Grocery Assistant MCP project as it moves beyond the initial read-only version and into safe write tools, relationship-aware data handling, and future planning intelligence.

The project is growing around three core data areas:

- **Inventory**: what food the user has, had, or wants to keep track of.
- **Intake**: what the user ate, including meals and meal components.
- **Waste**: food that was discarded, spoiled, expired, overbought, unused, or otherwise wasted.

The main development priority is to scaffold the project safely. Each version should add a clear layer of capability without introducing hidden side effects or data relationships that are difficult to test.

---

# Big Strategic Direction

The project should progress in controlled stages:

```text
Version 1.0:
Read-only MCP grocery assistant.

Version 1.1:
Safe write tools for inventory, intake, and waste.

Version 1.2:
Edit/delete tools for intake and relationship cleanup.

Version 1.3:
Controlled inventory consumption tools.

Version 1.4:
Batch meal logging and transaction-like workflows.

Version 1.5:
Planning intelligence: restock suggestions, meal suggestions, waste pattern review.
```

The key principle is:

> Version 1.1 should become the safe write foundation, not the full intelligent grocery automation layer.

---

# Current Data Model Direction

The project separates grocery data into purpose-specific CSV files:

```text
user_inventory.csv
user_food_waste.csv
user_intake_history.csv
user_intake_items.csv
```

This separation is intentional. Inventory, intake, and waste should not be forced into one table because they represent different concepts.

---

## Inventory

Inventory records food items that are useful for current or future grocery decisions.

Inventory can include:

- currently available items
- low-stock items
- empty or out-of-stock items kept as reminders
- expired items still physically present
- common staples
- items the user has purchased before

Out-of-stock items may still be useful because they help the assistant understand habits, common staples, restock patterns, and lower-priority items.

---

## Intake History

`user_intake_history.csv` records parent eating events.

Examples:

- breakfast
- lunch
- dinner
- snack
- post-workout meal
- takeaway meal
- leftover meal

Each row should describe the overall meal or eating event.

---

## Intake Items

`user_intake_items.csv` records the child components of a meal.

Example:

```text
intake_007  Dinner  Spaghetti bolognese
    ├── beef mince
    ├── spaghetti
    ├── tomato sauce
    └── parmesan
```

The relationship should be:

```text
user_intake_history.csv
    intake_id
        ↓
user_intake_items.csv
    intake_id
```

The `stock_id` field inside intake items should be optional. This allows an intake item to link to inventory when known, while still supporting restaurant food, takeaway, untracked ingredients, and estimated meals.

---

## Food Waste

Food waste records meaningful negative outcomes from food ownership.

Examples:

- expired
- spoiled
- discarded
- unused
- overbought
- did not like

In Version 1.1, food waste should be created through inventory removal workflows rather than through a standalone waste tool.

---

# Version 1.0 — Read-Only MCP Grocery Assistant

## Goal

Version 1.0 establishes the MCP server structure and exposes grocery data safely as read-only resources.

## Main Capabilities

- Read inventory data.
- Read intake data.
- Read grocery-related CSV resources.
- Test MCP resources using stdio, streamable HTTP, curl commands, and MCP Inspector.
- Establish the project package structure.

## Key Learning Focus

- Understanding MCP resources.
- Understanding server/client interaction.
- Understanding how JSON-RPC requests are sent through MCP.
- Testing resources before adding write tools.

---

# Version 1.1 — Safe Write Foundation

## Goal

Version 1.1 adds controlled write tools while keeping behaviour predictable, testable, and safe.

This version should focus on strong validation and clear boundaries rather than automation.

## Included Capabilities

### Inventory Write Tools

```text
search_inventory
add_inventory_item
update_inventory_item
remove_inventory_item
```

### Intake Write Tools

```text
add_intake_entry
add_intake_item
```

### Waste Handling

Food waste should be created only through `remove_inventory_item()` when the removal type is waste-related.

Waste-related removal types may include:

```text
expired
spoiled
discarded
unused
overbought
did_not_like
```

Non-waste removal types may include:

```text
used_up
duplicate_entry
incorrect_entry
test_entry
no_longer_tracked
unknown
```

## What Version 1.1 Should Not Do Yet

Version 1.1 should not yet:

- automatically deduct inventory when logging intake
- automatically create intake items from a meal description
- automatically infer food waste from leftovers
- automatically reconcile recipes, stock, intake, and shopping needs
- support complex edits or deletes of meals and meal components
- support batch meal logging with inventory deduction

These behaviours are useful, but they introduce more complex relationships and should be delayed until the core write foundation is stable.

---

## Version 1.1 Safety Rules

### Inventory Safety

Inventory write tools should enforce:

```text
- food_item is required
- quantity cannot be negative
- servings_remaining cannot be negative
- expiry_date must be YYYY-MM-DD or blank
- stock_status must be one of the allowed values
- stock_status="removed" should not be used for active inventory rows
- quantity=0 and servings_remaining=0 should not normally be stock_status="ok"
```

### Intake Safety

`add_intake_entry()` should enforce:

```text
- date is required
- meal_name is required
- date must be YYYY-MM-DD
- time must be HH:MM or blank
- meal_type must be valid
- nutrition numbers cannot be negative
- hunger ratings should stay within a sensible numeric range when provided
```

`add_intake_item()` should enforce:

```text
- intake_id is required
- intake_id must exist in user_intake_history.csv
- food_item is required
- stock_id is optional
- if stock_id is supplied, it must exist in user_inventory.csv
- nutrition numbers cannot be negative
- servings_used cannot be negative
```

### Waste Safety

Food waste creation should enforce:

```text
- waste is only created for meaningful waste outcomes
- waste should preserve inventory item details at time of removal
- quantity_wasted cannot be negative
- servings_wasted cannot be negative
- if waste quantity is not provided, use the current remaining quantity where possible
- estimated consumed amount should never go below zero
```

---

## Version 1.1 Testing Checklist

### Inventory Tests

```text
[ ] add_inventory_item works with valid data
[ ] add_inventory_item rejects blank food_item
[ ] add_inventory_item rejects negative quantity
[ ] add_inventory_item rejects invalid stock_status
[ ] add_inventory_item stores initial_quantity and initial_servings

[ ] update_inventory_item updates only provided fields
[ ] update_inventory_item rejects missing stock_id
[ ] update_inventory_item rejects unknown stock_id
[ ] update_inventory_item prevents invalid stock/quantity combinations

[ ] remove_inventory_item removes normal used_up item without creating waste
[ ] remove_inventory_item creates waste for expired/spoiled/discarded removal types
[ ] remove_inventory_item rejects unknown stock_id
[ ] remove_inventory_item rejects invalid removal_type
```

### Intake Tests

```text
[ ] add_intake_entry creates parent meal row
[ ] add_intake_entry rejects invalid date
[ ] add_intake_entry rejects invalid time
[ ] add_intake_entry rejects invalid meal_type
[ ] add_intake_entry rejects negative nutrition values

[ ] add_intake_item creates child row
[ ] add_intake_item rejects missing intake_id
[ ] add_intake_item rejects unknown intake_id
[ ] add_intake_item accepts blank stock_id
[ ] add_intake_item rejects unknown stock_id when supplied
[ ] add_intake_item rejects negative servings/nutrition values
```

### Resource and MCP Tests

```text
[ ] inventory resource still reads correctly
[ ] intake history resource still reads correctly
[ ] intake items resource still reads correctly
[ ] food waste resource reads correctly
[ ] MCP Inspector can call all Version 1.1 tools
[ ] curl commands are documented for key tool calls
```

---

# Version 1.2 — Relationship Editing and Cleanup

## Goal

Version 1.2 should add safe editing and removal for intake relationships.

## Possible New Tools

```text
update_intake_entry
update_intake_item
remove_intake_item
remove_intake_entry
```

## Main Design Question

If a parent meal is removed, what happens to its child intake items?

Options:

```text
Option A: block removal if child items exist
Option B: cascade delete child items
Option C: mark the meal as removed or cancelled
```

For a CSV-based system, the safest early approach is:

> Block removal if child items exist. Require child items to be removed first.

This avoids accidental data loss.

---

# Version 1.3 — Controlled Inventory Consumption

## Goal

Version 1.3 should introduce deliberate inventory consumption.

This is different from intake logging.

Eating something does not always mean inventory should automatically decrease. The food may be from a restaurant, takeaway, shared food, untracked ingredients, leftovers, or an uncertain portion.

## Possible New Tool

```text
consume_inventory_item(
    stock_id,
    quantity_used,
    servings_used,
    reason
)
```

## Recommended Behaviour

The tool should:

```text
- require a valid stock_id
- reduce quantity and/or servings_remaining
- prevent negative remaining stock
- update stock_status if the item becomes low, very low, empty, or out
- optionally link consumption to an intake_id or intake_item_id
```

This should stay separate from `add_intake_item()` at first.

A safe future workflow would be:

```text
1. add_intake_entry()
2. add_intake_item()
3. optionally consume_inventory_item()
```

---

# Version 1.4 — Batch Meal Logging

## Goal

Version 1.4 should allow higher-level meal logging workflows.

## Possible New Tool

```text
add_meal_with_items(
    meal_data,
    item_list
)
```

Later this may expand to:

```text
add_meal_with_items_and_inventory_updates()
```

## Risk

This version introduces multi-table writes:

```text
user_intake_history.csv
user_intake_items.csv
possibly user_inventory.csv
```

If the parent meal is written but a child item fails, the system may create partial data.

Before this version, the project should have a clear strategy for:

```text
- validation before writing
- rollback or cleanup
- partial write prevention
- clear error messages
```

---

# Version 1.5 — Planning Intelligence

## Goal

Version 1.5 should add smarter analysis and planning features after the write foundation is stable.

## Possible Capabilities

```text
suggest_restock_items
suggest_meals_from_inventory
suggest_use_soon_items
review_waste_patterns
review_intake_patterns
create_shopping_candidates
summarise_grocery_state
```

These should mostly begin as read/analysis tools or MCP prompts before they become write-heavy tools.

---

# Long-Term Design Principles

## Keep Write Tools Explicit

Avoid hidden side effects.

```text
Good:
add_intake_item() records what was eaten.

Risky:
add_intake_item() automatically deducts inventory, creates waste, updates shopping list, and changes stock status.
```

Automation should be added gradually and tested carefully.

---

## Keep MCP Tool Wrappers Thin

MCP tool files should:

```text
- describe tool parameters clearly
- call service-layer functions
- return clean JSON-ready dictionaries
```

They should not:

```text
- directly edit CSV files
- duplicate validation logic
- generate IDs
- contain complex grocery rules
```

Business logic should stay in the service layer.

---

## Keep Generic Helpers Generic

`write_helpers.py` should contain reusable validation and CSV helpers.

Good examples:

```text
clean_text
clean_lower_text
validate_non_negative_number
validate_date_or_blank
validate_time_or_blank
validate_int_range
backup_csv
read_csv_for_write
save_csv
generate_next_id
require_non_empty
```

Domain-specific rules should stay in service files, not generic helper files.

Examples of domain rules:

```text
VALID_STOCK_STATUSES
VALID_MEAL_TYPES
VALID_REMOVAL_TYPES
should_create_food_waste_record()
validate_inventory_stock_consistency()
```

---

## Use Consistent IDs

The project should use one consistent ID style.

Recommended style:

```text
inv_001
intake_001
intake_item_001
waste_001
```

Avoid mixing styles such as:

```text
INTAKE-0005
intake_005
inv_001
```

Consistency will make tests, examples, documentation, and debugging much easier.

---

# Recommended Documentation Files

The project documentation may eventually include:

```text
README.md
docs/project_roadmap.md
docs/version_1_1_write_tools.md
docs/data_model.md
docs/mcp_testing.md
docs/curl_examples.md
docs/development_journal.md
```

This roadmap can be stored as:

```text
docs/project_roadmap.md
```

or:

```text
docs/version_1_1_roadmap.md
```

---

# Final Direction

The strongest next step is to finish Version 1.1 as a reliable safe-write foundation.

Do not rush into automation yet.

Once inventory writes, intake parent-child writes, and waste creation are validated and tested, the later intelligent grocery assistant features will be much easier to build safely.
