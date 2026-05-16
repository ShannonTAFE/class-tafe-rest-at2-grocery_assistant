# Reviewed Version 1.1 curl request files

These JSON files are valid MCP JSON-RPC request bodies for manual curl testing.

## Important note about IDs

Some request files contain placeholder values:

```text
REPLACE_WITH_STOCK_ID_FROM_ADD_RESPONSE
REPLACE_WITH_INTAKE_ID_FROM_ADD_RESPONSE
```

Replace these with the IDs returned by earlier `add_inventory_item` or `add_intake_entry` calls.

Avoid relying on hardcoded `inv_001`, `inv_002`, or `intake_001` unless you know your current CSV state.

## Suggested manual sequence

```text
01_initialize.json
02_initialized_notification.json
03_resources_list.json
04_read_inventory.json
05_tools_list.json
06_prompts_list.json
07_add_inventory_item.json
04_read_inventory.json
11_search_inventory_fridge.json
12_add_yoghurt.json
13_update_item_TEMPLATE_REPLACE_STOCK_ID.json
14_remove_yoghurt_expired_TEMPLATE_REPLACE_STOCK_ID.json
16_read_food_waste.json
18_add_intake_entry.json
19_add_intake_item_TEMPLATE_REPLACE_INTAKE_ID.json
20_add_intake_item_invalid_intake_id.json
21_read_intake_history.json
22_read_intake_items.json
23_get_recent_intake.json
24_get_daily_intake_summary.json
```

## Negative validation checks

These should return MCP/tool errors, not successful item creation:

```text
08_add_inventory_missing_food_item.json
09_add_inventory_invalid_date.json
10_add_inventory_negative_quantity.json
20_add_intake_item_invalid_intake_id.json
```
