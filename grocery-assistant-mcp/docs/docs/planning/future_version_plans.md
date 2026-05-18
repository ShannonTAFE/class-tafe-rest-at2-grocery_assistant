# Future Version Plans

## Purpose

This file records ideas intentionally deferred beyond the Version 1.4 closeout baseline.

It should not describe Version 1.4 batch meal logging as future work. Version 1.4 now owns:

```text
add_meal_with_items
add_meal_with_inventory_items
```

---

# Version 1.5 — Planning Intelligence

Version 1.5 can begin adding recommendation and planning features on top of the safe write foundation.

Possible capabilities:

```text
suggest_meals_from_inventory
review_low_stock_items
suggest_restock_items
review_food_waste_patterns
draft_shopping_list
suggest_next_meal
review_recent_intake_patterns
```

Important rule:

```text
Planning tools may suggest, but should not silently mutate inventory or intake records.
```

---

# Future Shopping List Support

Possible files:

```text
user_shopping_list.csv
user_shopping_list_items.csv
```

Possible tools:

```text
add_shopping_list_item
update_shopping_list_item
remove_shopping_list_item
generate_shopping_list_from_low_stock
generate_shopping_list_from_meal_plan
```

Design questions:

- Should generated shopping items require confirmation?
- Should low-stock inventory automatically become shopping list entries?
- How should priority be represented?
- How should repeated staples be handled?

---

# Future Meal Templates and Learning

Possible files:

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
A known meal template can help create intake records, but inventory deduction should still require an explicit inventory-linked path.
```

---

# Future Consumption Adjustment and Reversal

Version 1.3 and Version 1.4 record inventory consumption events, but reversal rules are intentionally deferred.

Possible future tools:

```text
adjust_inventory_consumption
undo_inventory_consumption
restore_inventory_from_consumption
remove_intake_item_and_optionally_restore_inventory
```

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

Possible files:

```text
user_recipes.csv
user_recipe_items.csv
user_batch_cooks.csv
user_batch_cook_portions.csv
```

Possible tools:

```text
create_recipe
add_recipe_item
log_batch_cook
consume_recipe_portion
```

Design questions:

- How are recipe servings represented?
- How are leftovers tracked?
- Does one batch cook create inventory items, intake items, or both?
- How should partial ingredient deduction work?

---

# Future Nutrition Improvements

Possible ideas:

- nutrition estimate confidence scoring
- recipe-level nutrition rollups
- parent meal nutrition auto-sum from child items
- optional nutrition sources
- better handling of unknown estimates

Current rule remains:

```text
Do not silently overwrite user-entered nutrition totals unless the user asks for recalculation.
```

---

# Future MCP Agent Behaviour

Possible prompt and agent improvements:

- guide agents to search before updating
- guide agents to ask before deducting inventory
- guide agents to use intake-only workflow for ambiguous meal logging
- guide agents to use inventory-linked workflow only when stock IDs are known or confirmed
