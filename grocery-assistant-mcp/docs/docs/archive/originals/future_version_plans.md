# Future Version Plans

## Purpose

This file records ideas intentionally deferred beyond the current Version 1.3 implementation.

The goal is to keep future ideas visible without adding them too early to the safe write foundation.

---

# Current Completed Stage

## Version 1.3 — Controlled Inventory Consumption

Version 1.3 adds explicit inventory consumption tools and event logging.

Completed capabilities:

- consume tracked inventory without creating intake rows
- create intake items from tracked inventory
- reduce inventory quantity and/or servings
- record inventory consumption events
- link consumption events to intake items where relevant
- preserve quantity and unit on intake item rows
- use canonical inventory stock status values
- expose inventory consumption records as an MCP resource
- preserve the rule that ordinary intake logging does not silently deduct inventory

Version 1.3 intentionally does not add automatic reversal, recipe-level consumption, batch meal logging, shopping list generation, or planning intelligence.

---

# Version 1.4 — Batch Meal Logging and Transaction-Like Workflows

Version 1.4 may introduce higher-level meal logging.

Possible tools:

```text
add_meal_with_items(
    meal_data,
    item_list
)

add_meal_with_inventory_items(
    meal_data,
    inventory_item_list
)
```

Possible later version:

```text
add_recipe_meal_from_inventory(
    recipe_id,
    intake_data,
    servings
)
```

This requires careful validation because it may write to several files:

```text
user_intake_history.csv
user_intake_items.csv
user_inventory.csv
user_inventory_consumption.csv
```

Before implementing this, the project should confirm:

- all input data can be validated before any writes
- partial writes are prevented or rolled back
- errors clearly explain which item failed
- inventory is not deducted unless explicitly requested
- parent intake entries are not created without their intended child rows
- consumption events link back to the created intake items

---

# Future Consumption Adjustment and Reversal

Version 1.3 records consumption events but does not yet reverse or adjust them.

Possible future tools:

```text
adjust_inventory_consumption
undo_inventory_consumption
restore_inventory_from_consumption
remove_intake_item_and_optionally_restore_inventory
```

These should not be implemented until the rules are very clear.

Important questions:

- Should reversal restore quantity, servings, or both?
- What happens if inventory has since been updated manually?
- What if the original inventory item has been removed?
- Should reversal remove the intake item or only adjust inventory?
- Should the consumption event be deleted or marked as reversed?

A future consumption event schema may need fields such as:

```text
reversed_at
reversal_reason
reversed_by_consumption_id
```

---

# Future Recipe and Batch Cooking Support

Possible future files:

```text
user_recipes.csv
user_recipe_items.csv
user_batch_meals.csv
user_batch_meal_items.csv
```

Possible capabilities:

```text
create_recipe
add_recipe_item
log_batch_cook
consume_recipe_serving_from_inventory
log_leftovers
```

Recipe support should come after inventory consumption is stable because recipe workflows may deduct many inventory items at once.

---

# Future Shopping and Restock Support

Possible future files:

```text
user_shopping_list.csv
user_purchase_history.csv
```

Possible capabilities:

```text
suggest_restock_items
create_shopping_candidates
add_to_shopping_list
mark_shopping_item_purchased
review_purchase_patterns
```

Shopping support should use inventory, consumption, intake, and waste records together.

Example:

```text
A food that is often consumed and rarely wasted may be a strong restock candidate.
A food that is often wasted should be restocked cautiously.
A food that was bought once and never consumed should be low priority.
```

---

# Version 1.5 — Planning Intelligence

Version 1.5 should add smarter read/analysis features after the write foundation is stable.

Possible capabilities:

```text
suggest_restock_items
suggest_meals_from_inventory
suggest_use_soon_items
review_waste_patterns
review_consumption_patterns
review_intake_patterns
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

To support better advice, future waste analysis may use:

- original quantity
- amount consumed
- amount wasted
- expiry date
- purchase date
- reason wasted
- consumption history
- whether meal plans changed
- whether the item had a short shelf life
- whether the item was bought in bulk
- whether the user disliked it
- whether it was forgotten

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
