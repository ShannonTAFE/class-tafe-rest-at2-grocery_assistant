# Future Version Plans

## Purpose

This file records ideas intentionally deferred beyond the current Version 1.2 implementation.

The goal is to keep future ideas visible without adding them too early to the safe write foundation.

---

# Current Completed Stage

## Version 1.2 — Intake Relationship Editing and Cleanup

Version 1.2 adds safe intake search, editing, and cleanup tools.

Completed capabilities:

- search intake parent and child records
- update parent intake entries
- update child intake items
- remove child intake items
- remove parent intake entries only when safe
- block parent removal while child items exist
- preserve parent-child relationship safety

Version 1.2 intentionally does not add cascade delete, automatic inventory deduction, batch meal logging, shopping list generation, or planning intelligence.

---

# Version 1.3 — Controlled Inventory Consumption

Version 1.3 should introduce explicit inventory consumption.

Possible tools:

```text
consume_inventory_item(
    stock_id,
    quantity_used,
    servings_used,
    reason
)
adjust_inventory_quantity
mark_inventory_used_up
```

This tool should be separate from intake logging at first.

Eating a meal does not always mean tracked inventory should be reduced. The food may be from a restaurant, takeaway, shared food, leftovers, or untracked ingredients.

Safe workflow:

```text
1. add_intake_entry()
2. add_intake_item()
3. optionally consume_inventory_item()
```

Later, consumption may be linked to `intake_id` or `intake_item_id`.

---

# Version 1.4 — Batch Meal Logging

Version 1.4 may introduce higher-level meal logging.

Possible tools:

```text
add_meal_with_items(
    meal_data,
    item_list
)
```

Later version:

```text
add_meal_with_items_and_inventory_updates()
```

This requires careful validation because it writes to multiple files:

```text
user_intake_history.csv
user_intake_items.csv
possibly user_inventory.csv
```

Before implementing this, the project should have a strategy for:

- validating all data before writing
- preventing partial writes
- handling rollback or cleanup
- returning clear error messages

---

# Version 1.5 — Planning Intelligence

Version 1.5 should add smarter read/analysis features after the write foundation is stable.

Possible capabilities:

```text
suggest_restock_items
suggest_meals_from_inventory
suggest_use_soon_items
review_waste_patterns
review_intake_patterns
create_shopping_candidates
summarise_grocery_state
```

These should begin as prompts or read-only analysis tools before becoming write-heavy tools.

Important note:

Planning intelligence should use existing resources and tools but should not silently modify CSV files.

---

# Future Waste Pattern Learning

The food waste data can eventually help the assistant answer questions such as:

```text
What do I regularly waste?
What expires before I use it?
What should I buy less of?
Which foods do I keep buying but not eating?
What ingredients should I avoid bulk-buying?
```

The system should not give shallow advice such as:

```text
You wasted yoghurt. Buy less yoghurt.
```

Better future advice should consider the item lifecycle.

Example:

```text
You usually consume most of a 1kg tub of yoghurt, but often waste the last 100–200g.
A smaller tub may reduce waste, but only slightly.
The savings may not justify changing your habit unless this happens often.
```

To support better advice, future waste records may need context such as:

- original quantity
- amount consumed
- amount wasted
- expiry date
- purchase date
- reason wasted
- whether meal plans changed
- whether the item had a short shelf life
- whether the item was bought in bulk
- whether the user disliked it
- whether it was forgotten

This is why early versions record waste carefully but do not yet attempt advanced waste pattern analysis.

---

# Long-Term Principle

Future automation should be added only when the underlying data relationships are safe, tested, and understandable.

The project should continue to prefer:

```text
explicit tools
clear validation
small version increments
well-documented boundaries
```
