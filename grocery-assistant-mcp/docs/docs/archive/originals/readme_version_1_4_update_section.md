# README Update Section — Version 1.4

## Version 1.4 Capabilities

Version 1.4 adds safe batch meal workflows on top of the existing inventory, intake, consumption, and waste-tracking foundations.

Version 1.4 is split into three stages:

```text
Version 1.4A — Core service refactor
Version 1.4B — Intake-only batch meal logging
Version 1.4C — Inventory-linked batch meal logging
```

### Version 1.4A — Core Refactor

The service layer was refactored into focused helper modules so future workflows can coordinate multiple CSV files without overloading `grocery_service.py`.

Key extracted modules include:

```text
schemas.py
constants.py
service_utils.py
csv_store.py
inventory_rules.py
intake_helpers.py
consumption_helpers.py
waste_helpers.py
relationship_helpers.py
transaction_helpers.py
write_helpers.py
```

The refactor preserved existing behaviour while preparing the project for batch workflows.

### Version 1.4B — `add_meal_with_items`

Adds intake-only batch meal logging.

This tool creates:

```text
1 parent intake entry
multiple child intake item rows
```

It does not:

```text
deduct inventory
create inventory consumption records
create food waste records
auto-create meal templates
auto-learn aliases
```

Use this when a user describes a meal with multiple components but does not explicitly want inventory updated.

Example:

```text
I had oats with milk and banana.
```

Expected effect:

```text
user_intake_history.csv      +1 parent meal row
user_intake_items.csv        +multiple child item rows
user_inventory.csv           unchanged
user_inventory_consumption.csv unchanged
user_food_waste.csv          unchanged
```

### Version 1.4C — `add_meal_with_inventory_items`

Adds explicit inventory-linked batch meal logging.

This tool creates:

```text
1 parent intake entry
multiple child intake item rows
selected inventory deductions
linked inventory consumption records
```

It writes to:

```text
user_intake_history.csv
user_intake_items.csv
user_inventory.csv
user_inventory_consumption.csv
```

It does not write to:

```text
user_food_waste.csv
```

Use this only when inventory involvement is explicit.

Example:

```text
Log spaghetti bolognese using 100g spaghetti from inv_001 and 125g beef mince from inv_002. Add parmesan as untracked.
```

Expected effect:

```text
user_intake_history.csv        +1 parent meal row
user_intake_items.csv          +inventory-linked and manual child rows
user_inventory.csv             selected stock rows reduced
user_inventory_consumption.csv +linked consumption rows
user_food_waste.csv            unchanged
```

### Important Version 1.4 Rule

```text
Meal recognition and inventory consumption are separate decisions.
```

A request such as:

```text
I ate spag bog.
```

should not automatically deduct inventory.

A request such as:

```text
Log spag bog and update inventory using inv_001 and inv_002.
```

can use the explicit inventory-linked batch workflow.
