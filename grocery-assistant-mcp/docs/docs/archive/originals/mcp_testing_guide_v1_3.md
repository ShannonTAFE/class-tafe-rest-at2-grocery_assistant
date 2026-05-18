# MCP Testing Guide — Version 1.3

## Purpose

This guide records manual testing steps for Version 1.3 controlled inventory consumption workflows.

Version 1.3 should be tested with:

```text
automated pytest suite
MCP Inspector
curl / Streamable HTTP checks
```

Automated tests validate service behaviour. MCP Inspector and curl validate that the MCP server exposes the tools and resources correctly.

Run automated tests from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

---

# Start the Server

From the project root:

```powershell
.\.venv\Scripts\python.exe -m grocery_assistant_mcp.streamable_http_server
```

Expected MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

A browser request to `/` may return `404 Not Found`.

A browser request to `/mcp` may return `406 Not Acceptable`.

This is expected because the MCP endpoint expects MCP JSON-RPC requests, not normal browser page requests.

## Opening MCP Inspector

MCP Inspector is used as a local testing client for the Grocery Assistant MCP server.

```powershell
npx @modelcontextprotocol/inspector
```
It allows us to:

- connect to the running MCP server
- view registered tools, resources, and prompts
- manually call MCP tools
- inspect request and response payloads
- confirm that tool behaviour matches the service-layer tests
---

# MCP Inspector Checklist

## Tool List

Confirm these Version 1.3 tools are listed:

```text
consume_inventory_item
add_intake_item_from_inventory
```

Confirm existing tools are still listed:

```text
search_inventory
add_inventory_item
update_inventory_item
remove_inventory_item
get_recent_intake
get_daily_intake_summary
search_intake
add_intake_entry
add_intake_item
update_intake_entry
update_intake_item
remove_intake_item
remove_intake_entry
```

---

## Resource List

Confirm this Version 1.3 resource is listed:

```text
grocery://inventory-consumption
```

Confirm existing resources still work:

```text
grocery://inventory
grocery://intake/history
grocery://intake/items
grocery://intake-items
grocery://food-waste
grocery://food-waste/expired
```

---

# Test Flow A — Inventory-Only Consumption

## Step 1: Find inventory item

Call:

```json
{
  "query": "milk",
  "category": "",
  "location": ""
}
```

Tool:

```text
search_inventory
```

Copy a valid `stock_id`.

## Step 2: Consume inventory

Call:

```json
{
  "stock_id": "inv_002",
  "quantity_used": 500,
  "servings_used": 0,
  "consumption_type": "consumed",
  "tracking_confidence": "medium",
  "notes": "MCP Inspector test: drank 500ml of milk"
}
```

Tool:

```text
consume_inventory_item
```

Expected result:

```text
success = true
inventory quantity decreases
inventory_after shows updated quantity
consumption_record is returned
consumption_record.intake_id is blank
consumption_record.intake_item_id is blank
no intake item is created
no food waste record is created
```

## Step 3: Verify inventory changed

Call `search_inventory` again for the same item.

Expected:

```text
quantity is reduced
stock_status remains in_stock unless depleted
```

## Step 4: Verify consumption event

Read:

```text
grocery://inventory-consumption
```

Expected:

```text
new consumption event exists
stock_id matches consumed item
quantity_used matches tool call
consumption_type matches tool call
```

---

# Test Flow B — Intake-Linked Consumption

## Step 1: Create or find parent intake entry

Call `search_intake` to find a parent meal.

If needed, create one with `add_intake_entry`:

```json
{
  "date": "2026-05-17",
  "meal_name": "Version 1.3 test meal",
  "time": "18:30",
  "meal_type": "dinner",
  "meal_description": "Testing controlled inventory consumption",
  "source": "home",
  "amount_eaten": "1 plate",
  "portion_confidence": "medium",
  "total_calories_estimate": 0,
  "total_protein_g_estimate": 0,
  "total_carbs_g_estimate": 0,
  "total_fat_g_estimate": 0,
  "total_fibre_g_estimate": 0,
  "total_sugar_g_estimate": 0,
  "total_sodium_mg_estimate": 0,
  "nutrition_confidence": "medium",
  "was_finished": "unknown",
  "leftovers_created": "unknown",
  "hunger_before": "",
  "hunger_after": "",
  "notes": "Parent meal for Version 1.3 testing"
}
```

Copy the returned `intake_id`.

## Step 2: Add intake item from inventory

Call:

```json
{
  "intake_id": "intake_001",
  "stock_id": "inv_002",
  "amount_eaten": "500 ml",
  "quantity_used": 500,
  "servings_used": 0,
  "calories_estimate": 250,
  "protein_g_estimate": 17,
  "carbs_g_estimate": 24,
  "fat_g_estimate": 9,
  "fibre_g_estimate": 0,
  "sugar_g_estimate": 24,
  "sodium_mg_estimate": 200,
  "nutrition_confidence": "medium",
  "consumption_type": "consumed",
  "tracking_confidence": "medium",
  "notes": "Milk consumed with meal"
}
```

Tool:

```text
add_intake_item_from_inventory
```

Expected result:

```text
success = true
intake_item is returned
intake_item.source = inventory
intake_item.stock_id matches selected stock_id
intake_item.quantity_used = 500
intake_item.unit copied from inventory
inventory quantity decreases
consumption_record is returned
consumption_record.intake_id matches parent
consumption_record.intake_item_id matches created child item
no food waste record is created
```

## Step 3: Verify intake relationship

Call `search_intake`:

```json
{
  "query": "",
  "intake_id": "intake_001",
  "intake_item_id": "",
  "date": "",
  "date_from": "",
  "date_to": "",
  "meal_type": "",
  "source": "",
  "stock_id": "",
  "category": "",
  "limit": 20
}
```

Expected:

```text
new child item appears
child item has stock_id
child item has quantity_used and unit
```

## Step 4: Verify consumption event

Read:

```text
grocery://inventory-consumption
```

Expected:

```text
new linked consumption event exists
intake_id is populated
intake_item_id is populated
stock_id is populated
quantity_before and quantity_after are populated
```

---

# Negative Test — Over-Consumption

Call:

```json
{
  "stock_id": "inv_002",
  "quantity_used": 999999,
  "servings_used": 0,
  "consumption_type": "consumed",
  "tracking_confidence": "medium",
  "notes": "Should fail"
}
```

Tool:

```text
consume_inventory_item
```

Expected:

```text
tool error
quantity_used cannot exceed current quantity
inventory remains unchanged
no consumption event is created
```

---

# Negative Test — Invalid Stock Status

If a seed row still uses an old status such as `ok`, Version 1.3 should reject it.

Expected error:

```text
stock_status must be one of: expired, in_stock, low, out, very_low
```

Fix the seed row rather than supporting old aliases.

---

# Suggested Curl Checks

Use curl after MCP Inspector succeeds.

Test sequence:

```text
initialize session
send initialized notification
tools/list
resources/list
tools/call search_inventory
tools/call consume_inventory_item
resources/read grocery://inventory-consumption
tools/call add_intake_item_from_inventory
tools/call search_intake
```

Record any curl-specific issues in the development journal or completion checklist.
