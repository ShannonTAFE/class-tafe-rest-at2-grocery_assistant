# MCP Testing Guide — Version 1.4

## Purpose

This guide records manual and automated testing steps for Version 1.4.

Version 1.4 includes:

```text
Version 1.4A — Core service refactor
Version 1.4B — Batch meal logging
Version 1.4C — Batch inventory-linked meal logging planning
```

Automated tests validate service behaviour. MCP Inspector validates that the MCP server exposes the tools correctly and that manual tool calls behave as expected.

---

# Automated Test Commands

Run the full suite from the project root:

```powershell
pytest -q
```

Run the Version 1.4B batch meal tests:

```powershell
pytest tests/test_batch_meal_service.py -q
```

Run MCP registration tests:

```powershell
pytest tests/test_mcp_tool_registration.py -q
```

If Windows temp/cache folders become locked, use:

```powershell
pytest -q --basetemp "$env:TEMP\pytest-grocery-full"
```

---

# Opening MCP Inspector

MCP Inspector is used as a local testing client for the Grocery Assistant MCP server.

It allows us to:

```text
connect to the running MCP server
view registered tools, resources, and prompts
manually call MCP tools
inspect request and response payloads
confirm tool behaviour matches service-layer tests
```

## Step 1 — Start the Streamable HTTP Server

From the project root:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected endpoint:

```text
http://127.0.0.1:8000/mcp
```

Leave this terminal open while using MCP Inspector.

A browser request to `/` may return:

```text
404 Not Found
```

A browser request to `/mcp` may return:

```text
406 Not Acceptable
```

This is expected because the MCP endpoint expects MCP protocol requests, not normal browser page requests.

## Step 2 — Open MCP Inspector

In a second terminal:

```powershell
npx @modelcontextprotocol/inspector
```

If prompted to install the package, accept the prompt.

## Step 3 — Connect to the Local MCP Server

Use:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
```

After connecting, MCP Inspector should show available tools, resources, and prompts.

---

# Version 1.4B Tool Checklist

Confirm this tool appears:

```text
add_meal_with_items
```

This tool should be described as an intake-only batch meal logging tool.

It should not be described as an inventory deduction or recipe consumption tool.

---

# Test Flow A — Batch Meal Logging Without Inventory Deduction

## Tool

```text
add_meal_with_items
```

## MCP Inspector Input

Paste only the tool arguments into MCP Inspector.

Do not paste the full JSON-RPC wrapper.

```json
{
  "meal_data": {
    "date": "2026-05-18",
    "time": "18:30",
    "meal_type": "dinner",
    "meal_name": "Spaghetti bolognese",
    "meal_description": "Home cooked spaghetti bolognese",
    "source": "home",
    "amount_eaten": "1 bowl",
    "portion_confidence": "medium",
    "total_calories_estimate": 760,
    "total_protein_g_estimate": 42,
    "total_carbs_g_estimate": 86,
    "total_fat_g_estimate": 25,
    "total_fibre_g_estimate": 8,
    "total_sugar_g_estimate": 10,
    "total_sodium_mg_estimate": 650,
    "nutrition_confidence": "medium",
    "was_finished": "yes",
    "leftovers_created": "no",
    "hunger_before": "hungry",
    "hunger_after": "satisfied",
    "notes": "Version 1.4B MCP Inspector test"
  },
  "items": [
    {
      "food_item": "Spaghetti",
      "category": "pantry",
      "source": "home",
      "amount_eaten": "1 serve",
      "quantity_used": 100,
      "unit": "g",
      "servings_used": 1,
      "calories_estimate": 360,
      "protein_g_estimate": 12,
      "carbs_g_estimate": 72,
      "fat_g_estimate": 2,
      "fibre_g_estimate": 4,
      "sugar_g_estimate": 2,
      "sodium_mg_estimate": 10,
      "nutrition_confidence": "medium",
      "notes": "Child item test"
    },
    {
      "food_item": "Beef mince",
      "category": "protein",
      "source": "home",
      "amount_eaten": "1 serve",
      "quantity_used": 125,
      "unit": "g",
      "servings_used": 1,
      "calories_estimate": 300,
      "protein_g_estimate": 28,
      "carbs_g_estimate": 0,
      "fat_g_estimate": 20,
      "fibre_g_estimate": 0,
      "sugar_g_estimate": 0,
      "sodium_mg_estimate": 90,
      "nutrition_confidence": "medium",
      "notes": "Child item test"
    },
    {
      "food_item": "Tomato sauce",
      "category": "pantry",
      "source": "home",
      "amount_eaten": "1 serve",
      "quantity_used": 150,
      "unit": "g",
      "servings_used": 1,
      "calories_estimate": 80,
      "protein_g_estimate": 2,
      "carbs_g_estimate": 12,
      "fat_g_estimate": 2,
      "fibre_g_estimate": 3,
      "sugar_g_estimate": 8,
      "sodium_mg_estimate": 500,
      "nutrition_confidence": "medium",
      "notes": "Child item test"
    }
  ]
}
```

## Expected Response

```text
success = true
item_count = 3
inventory_deducted = false
consumption_records_created = 0
food_waste_records_created = 0
```

## Expected CSV Changes

```text
user_intake_history.csv:
    one new parent meal row

user_intake_items.csv:
    three new child item rows linked to the parent intake_id

user_inventory.csv:
    unchanged

user_inventory_consumption.csv:
    unchanged

user_food_waste.csv:
    unchanged
```

---

# MCP Inspector vs curl

MCP Inspector expects only tool arguments:

```json
{
  "meal_data": {},
  "items": []
}
```

curl requires the full JSON-RPC wrapper:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "add_meal_with_items",
    "arguments": {
      "meal_data": {},
      "items": []
    }
  }
}
```

---

# Version 1.4C Testing Preparation

Version 1.4C should not reuse the Version 1.4B test flow as proof of inventory deduction.

Version 1.4B proves:

```text
batch intake rows can be created safely
inventory is not deducted
consumption records are not created
```

Version 1.4C must add separate tests for:

```text
inventory-linked batch request validation
aggregate duplicate stock_id validation
inventory before/after state changes
linked consumption event creation
no partial writes across four CSV files
```
