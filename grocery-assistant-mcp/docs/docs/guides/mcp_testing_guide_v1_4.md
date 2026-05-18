# MCP Testing Guide — Version 1.4 Final

## Purpose

This guide verifies the final Version 1.4 MCP workflows from a clean dataset.

Version 1.4 includes:

```text
Version 1.4A — Core service refactor
Version 1.4B — Intake-only batch meal logging
Version 1.4C — Inventory-linked batch meal logging
```

The final closeout goal is to confirm:

```text
add_meal_with_items
    creates one parent intake entry and multiple child intake items
    does not deduct inventory

add_meal_with_inventory_items
    creates one parent intake entry and multiple child intake items
    deducts only explicitly selected inventory items
    creates linked inventory consumption records
```

---

## Preconditions

Run from the project root:

```powershell
pytest -q
```

Expected result:

```text
all tests pass
```

If testing from a clean dataset, reset the tracked CSV files to header rows only before starting the MCP curl workflow.

Tracked CSV files usually include:

```text
user_inventory.csv
user_intake_history.csv
user_intake_items.csv
user_inventory_consumption.csv
user_food_waste.csv
```

---

# Start the MCP Server

From the project root:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected endpoint:

```text
http://127.0.0.1:8000/mcp
```

Leave this terminal open.

A browser request to `/` may return `404 Not Found`.

A browser request to `/mcp` may return `406 Not Acceptable`.

Both are expected because the MCP endpoint expects protocol requests.

---

# MCP Inspector Verification

Open a second terminal:

```powershell
npx @modelcontextprotocol/inspector
```

Connect with:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
```

Verify the following tools are visible:

```text
search_inventory
add_inventory_item
update_inventory_item
remove_inventory_item
get_recent_intake
get_daily_intake_summary
add_intake_entry
add_intake_item
update_intake_entry
update_intake_item
remove_intake_entry
remove_intake_item
search_intake
consume_inventory_item
add_intake_item_from_inventory
add_meal_with_items
add_meal_with_inventory_items
```

The exact list may include additional tools if later versions have begun, but the two Version 1.4 batch tools must be present.

---

# Curl Workflow

The final Version 1.4 curl requests are located here:

```text
version_1_4/curl_requests/
```

The command reference explains how to initialize a session and save clean JSON response files:

```text
docs/guides/command_reference_v1_4.md
```

Recommended response folder:

```text
version_1_4/curl_responses/
```

For each request, save:

```text
*.raw.txt
*.json
```

The `.raw.txt` file contains the streamable HTTP wrapper.

The `.json` file contains the extracted JSON-RPC response.

---

# Final Curl Test Order

Run the requests in this order.

## 1. MCP protocol setup

```text
00_initialize.json
01_initialized_notification.json
```

## 2. Server inspection

```text
02_list_tools.json
03_list_resources.json
```

Expected:

```text
Tools and resources are registered.
Version 1.4 batch tools are visible.
```

## 3. Seed inventory

```text
inventory/10_add_inventory_spaghetti.json
inventory/11_add_inventory_beef_mince.json
inventory/12_add_inventory_tomato_sauce.json
inventory/13_search_inventory_all.json
inventory/14_search_inventory_protein.json
```

Expected from a clean dataset:

```text
inv_001 = Spaghetti
inv_002 = Beef mince
inv_003 = Tomato pasta sauce
```

Always verify actual IDs before using update or inventory-linked batch requests.

## 4. Confirm update workflow still works

```text
inventory/15_update_inventory_beef_mince_low.json
inventory/16_search_inventory_low_stock.json
```

Expected:

```text
Beef mince is updated to low stock.
```

## 5. Test Version 1.4B intake-only batch workflow

```text
batch_meals/20_add_meal_with_items_intake_only.json
```

Expected:

```text
One parent intake entry is created.
Multiple child intake items are created.
Inventory is not deducted.
Inventory consumption records are not created.
Food waste records are not created.
```

## 6. Test Version 1.4C inventory-linked batch workflow

```text
batch_meals/21_add_meal_with_inventory_items_spag_bog.json
```

Expected:

```text
One parent intake entry is created.
Inventory-linked child intake items are created.
Manual child intake items may also be created.
Selected inventory quantities/servings are deducted.
Linked inventory consumption records are created.
Food waste records are not created.
```

Important:

```text
This request assumes the clean-dataset inventory IDs above:
inv_001 = Spaghetti
inv_002 = Beef mince
inv_003 = Tomato pasta sauce
```

If your IDs differ, update the request before running it.

## 7. Search and inspect resulting records

```text
intake/30_search_intake_by_date.json
intake/31_search_intake_spaghetti.json
resources/40_read_inventory_resource.json
resources/41_read_intake_history_resource.json
resources/42_read_intake_items_resource.json
resources/43_read_inventory_consumption_resource.json
resources/44_read_food_waste_resource.json
```

Expected:

```text
Inventory shows deductions from explicit inventory-linked workflow.
Intake history shows parent meals.
Intake items show child rows.
Inventory consumption shows linked usage events.
Food waste should remain empty unless removal/waste tests were run.
```

## 8. Validation checks

```text
validation/50_add_inventory_missing_food_item.json
validation/51_add_inventory_negative_quantity.json
validation/52_update_inventory_unknown_id.json
validation/53_add_intake_invalid_date.json
```

Expected:

```text
Each invalid request fails safely.
The server stays running.
CSV files remain valid.
```

---

# Version 1.4 Closeout Evidence

For final closeout, keep or screenshot evidence for:

```text
pytest -q passes
tools/list includes Version 1.4 tools
resources/list includes expected resources
add_meal_with_items succeeds
add_meal_with_inventory_items succeeds
inventory changed only in inventory-linked workflow
inventory consumption records were created only in inventory-linked workflow
validation requests failed safely
```

---

# Known Notes

## Hunger fields

`hunger_before` and `hunger_after` are flexible text fields.

Use string values such as:

```json
"hunger_before": "hungry",
"hunger_after": "satisfied"
```

Avoid numeric-only values in curl requests unless the tool schema has been changed to accept numbers.

## Resource URI names

If a resource read request fails, run:

```text
03_list_resources.json
```

Then update the URI in the corresponding file under:

```text
version_1_4/curl_requests/resources/
```
