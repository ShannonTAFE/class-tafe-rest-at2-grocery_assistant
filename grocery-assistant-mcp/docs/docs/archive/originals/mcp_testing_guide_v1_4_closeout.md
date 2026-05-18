# MCP Testing Guide — Version 1.4 Closeout

## Purpose

This guide verifies the final Version 1.4 MCP workflows.

It covers:

- opening MCP Inspector
- running streamable HTTP server
- testing `add_meal_with_items`
- testing `add_meal_with_inventory_items`
- running the curl-based full workflow from a fresh empty dataset

---

## Version 1.4 Tools to Verify

```text
add_meal_with_items
add_meal_with_inventory_items
```

`add_meal_with_items` is intake-only batch meal logging.

`add_meal_with_inventory_items` is explicit inventory-linked batch meal logging.

---

## Start the Server

From the project root:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Use this endpoint:

```text
http://127.0.0.1:8000/mcp
```

---

## Open MCP Inspector

In a second terminal:

```powershell
npx @modelcontextprotocol/inspector
```

Connect with:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
```

After connection, verify these sections appear:

```text
Tools
Resources
Prompts
```

---

## MCP Inspector Test — Version 1.4B

Select:

```text
add_meal_with_items
```

Paste only the tool arguments:

```json
{
  "meal_data": {
    "date": "2026-05-18",
    "time": "12:30",
    "meal_type": "lunch",
    "meal_name": "Oats with milk and banana",
    "source": "home",
    "amount_eaten": "1 bowl",
    "portion_confidence": "medium",
    "nutrition_confidence": "medium",
    "was_finished": "yes",
    "leftovers_created": "no",
    "notes": "Version 1.4B intake-only batch test"
  },
  "items": [
    {
      "food_item": "Oats",
      "category": "pantry",
      "source": "home",
      "amount_eaten": "1 serve",
      "quantity_used": 50,
      "unit": "g",
      "servings_used": 1,
      "nutrition_confidence": "medium"
    },
    {
      "food_item": "Milk",
      "category": "dairy",
      "source": "home",
      "amount_eaten": "1 splash",
      "quantity_used": 150,
      "unit": "ml",
      "servings_used": 1,
      "nutrition_confidence": "medium"
    },
    {
      "food_item": "Banana",
      "category": "fruit",
      "source": "home",
      "amount_eaten": "1 banana",
      "quantity_used": 1,
      "unit": "piece",
      "servings_used": 1,
      "nutrition_confidence": "medium"
    }
  ]
}
```

Expected result:

```text
success = true
inventory_deducted = false
consumption_records_created = 0
food_waste_records_created = 0
```

---

## MCP Inspector Test — Version 1.4C

Select:

```text
add_meal_with_inventory_items
```

Paste only the tool arguments:

```json
{
  "meal_data": {
    "date": "2026-05-18",
    "time": "18:30",
    "meal_type": "dinner",
    "meal_name": "Spaghetti bolognese",
    "source": "home",
    "amount_eaten": "1 bowl",
    "portion_confidence": "medium",
    "nutrition_confidence": "medium",
    "was_finished": "yes",
    "leftovers_created": "no",
    "notes": "Version 1.4C inventory-linked batch test"
  },
  "inventory_items": [
    {
      "stock_id": "inv_001",
      "amount_eaten": "1 serve",
      "quantity_used": 100,
      "servings_used": 1,
      "consumption_type": "used_in_cooking",
      "tracking_confidence": "medium",
      "nutrition_confidence": "medium",
      "notes": "Spaghetti from inventory"
    },
    {
      "stock_id": "inv_002",
      "amount_eaten": "1 serve",
      "quantity_used": 125,
      "servings_used": 1,
      "consumption_type": "used_in_cooking",
      "tracking_confidence": "medium",
      "nutrition_confidence": "medium",
      "notes": "Beef mince from inventory"
    }
  ],
  "manual_items": [
    {
      "food_item": "Parmesan",
      "category": "dairy",
      "source": "home",
      "amount_eaten": "small topping",
      "quantity_used": 10,
      "unit": "g",
      "nutrition_confidence": "low",
      "notes": "Manual untracked topping"
    }
  ],
  "consumption_type": "used_in_cooking",
  "tracking_confidence": "medium",
  "notes": "Version 1.4C MCP Inspector test"
}
```

Expected result:

```text
success = true
inventory_deducted = true
item_count = 3
inventory_item_count = 2
manual_item_count = 1
consumption_records_created = 2
food_waste_records_created = 0
```

---

## Curl Workflow

For full curl testing, use:

```text
docs/curl_requests/v1_4/
```

Follow:

```text
docs/version_1_4_final_test_plan.md
```

The curl workflow starts from a fresh empty dataset, seeds inventory, runs Version 1.4B, runs Version 1.4C, and inspects all affected resources.
