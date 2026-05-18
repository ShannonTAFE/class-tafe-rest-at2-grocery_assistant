# Version 1.4 Curl Requests

These requests support the final Version 1.4 closeout workflow.

Run from a clean dataset where tracked CSVs contain headers only.

Important ID assumption for the inventory-linked batch request:

```text
inv_001 = Spaghetti
inv_002 = Beef mince
inv_003 = Tomato pasta sauce
```

This is expected only when the inventory seed requests are run first from an empty dataset.

If IDs differ, update:

```text
batch_meals/21_add_meal_with_inventory_items_spag_bog.json
inventory/15_update_inventory_beef_mince_low.json
```

Use `02_list_tools.json` and `03_list_resources.json` before running workflow requests.
