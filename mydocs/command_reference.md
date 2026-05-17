# Command Reference — Version 1.3

## Project Root

Typical project root:

```powershell
cd C:\Users\shann\TafeLocal\rest-at2\grocery-assistant-mcp
```

---

# Python / Pytest

Run the full test suite:

```powershell
pytest -q
```

Run Version 1.3 focused tests:

```powershell
pytest tests/test_inventory_consumption.py -q
```

Run data, path, and resource tests:

```powershell
pytest tests/test_data_files.py tests/test_paths.py tests/test_mcp_resource_registration.py tests/test_resource_payloads.py -q
```

Run MCP tool registration tests:

```powershell
pytest tests/test_mcp_tool_registration.py -q
```

Run intake relationship tests:

```powershell
pytest tests/test_intake_edit_delete_service.py -q
pytest tests/test_search_intake_service.py -q
```

---

# MCP Servers

Run stdio server:

```powershell
python -m grocery_assistant_mcp.stdio_server
```

Run streamable HTTP server:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected HTTP endpoint:

```text
http://127.0.0.1:8000/mcp
```

---

# MCP Inspector

Use MCP Inspector to confirm tools and resources.

Version 1.3 tools:

```text
consume_inventory_item
add_intake_item_from_inventory
```

Version 1.3 resource:

```text
grocery://inventory-consumption
```

---

# Example Tool Arguments

## consume_inventory_item

```json
{
  "stock_id": "inv_002",
  "quantity_used": 500,
  "servings_used": 0,
  "consumption_type": "consumed",
  "tracking_confidence": "medium",
  "notes": "I drank 500ml of milk"
}
```

## add_intake_item_from_inventory

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

---

# Git

Suggested branch name:

```text
feature/version-1.3-controlled-consumption
```

Suggested commit message:

```text
feat: add controlled inventory consumption workflows
```

Suggested final docs commit:

```text
docs: update documentation for version 1.3
```
