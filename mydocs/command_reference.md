# Grocery Assistant MCP Command Reference

## Purpose

This file collects common commands used during development and testing of the Grocery Assistant MCP project.

Run most commands from the project root:

```powershell
cd C:\Users\shann\TafeLocal\rest-at2\grocery-assistant-mcp
```

---

# Run Tests

Run the full test suite:

```powershell
pytest -q
```

Run a specific test file:

```powershell
pytest tests/test_v1_1_write_foundation.py -q
```

Run MCP registration tests:

```powershell
pytest tests/test_mcp_tool_registration.py -q
```

---

# Run the MCP Stdio Server

Run the stdio server directly:

```powershell
python -m grocery_assistant_mcp.stdio_server
```

This is useful when testing a local MCP stdio connection.

---

# Run Stdio Server Through MCP Inspector

From the project root:

```powershell
npx @modelcontextprotocol/inspector .\.venv\Scripts\python.exe -m grocery_assistant_mcp.stdio_server
```

This launches MCP Inspector and connects it to the stdio server.

---

# Open MCP Inspector Manually

```powershell
npx @modelcontextprotocol/inspector
```

Use this when you want to manually configure the server connection inside the Inspector UI.

---

# Run the Streamable HTTP Server

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected endpoint:

```text
http://127.0.0.1:8000/mcp
```

Browser checks may show:

```text
GET /      -> 404 Not Found
GET /mcp   -> 406 Not Acceptable
```

This is expected. `/mcp` expects MCP JSON-RPC requests with the correct headers.

---

# Connect MCP Inspector to HTTP Server

Use these MCP Inspector settings:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
```

---

# PowerShell Curl Variables

In a second terminal, set:

```powershell
$BaseUrl = "http://127.0.0.1:8000"
$McpUrl = "$BaseUrl/mcp"

$ContentType = "Content-Type: application/json"
$Accept = "Accept: application/json, text/event-stream"
$ProtocolVersion = "MCP-Protocol-Version: 2025-06-18"
```

---

# Curl Request Files

Suggested folder:

```text
curl_requests/
```

Suggested request files:

```text
01_initialize.json
02_initialized_notification.json
03_resources_list.json
04_read_inventory.json
05_tools_list.json
06_prompts_list.json
07_add_inventory_item.json
08_update_inventory_item.json
09_remove_inventory_item.json
10_add_intake_entry.json
11_add_intake_item.json
```

---

# Initialize MCP Session

Request file:

```text
curl_requests/01_initialize.json
```

Command:

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  --data-binary "@curl_requests/01_initialize.json"
```

After this succeeds, copy the returned session ID.

Example:

```text
mcp-session-id: 7ab88075d6744da99d21802e73b6b74a
```

Set:

```powershell
$McpSessionId = "7ab88075d6744da99d21802e73b6b74a"
```

---

# Send Initialized Notification

Request file:

```text
curl_requests/02_initialized_notification.json
```

Command:

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H "mcp-session-id: $McpSessionId" `
  --data-binary "@curl_requests/02_initialized_notification.json"
```

Purpose:

```text
Completes the MCP session setup after initialize.
```

---

# List Resources

Request file:

```text
curl_requests/03_resources_list.json
```

Command:

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H "mcp-session-id: $McpSessionId" `
  --data-binary "@curl_requests/03_resources_list.json"
```

Expected resources may include:

```text
grocery://inventory
grocery://intake/history
grocery://intake/items
grocery://food-waste
grocery://food-waste/expired
```

---

# Read Inventory

Request file:

```text
curl_requests/04_read_inventory.json
```

Command:

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H "mcp-session-id: $McpSessionId" `
  --data-binary "@curl_requests/04_read_inventory.json"
```

This confirms:

```text
MCP HTTP request -> resource layer -> service layer -> inventory CSV -> JSON response
```

---

# List Tools

Request file:

```text
curl_requests/05_tools_list.json
```

Command:

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H "mcp-session-id: $McpSessionId" `
  --data-binary "@curl_requests/05_tools_list.json"
```

Expected Version 1.1 tools include:

```text
search_inventory
add_inventory_item
update_inventory_item
remove_inventory_item
get_recent_intake
get_daily_intake_summary
add_intake_entry
add_intake_item
```

---

# List Prompts

Request file:

```text
curl_requests/06_prompts_list.json
```

Command:

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H "mcp-session-id: $McpSessionId" `
  --data-binary "@curl_requests/06_prompts_list.json"
```

Expected prompts may include:

```text
summarise_inventory
find_inventory_items
suggest_meals_from_inventory
review_recent_intake
review_daily_intake
suggest_next_meal
```

---

# Test Add Inventory Item

Request file:

```text
curl_requests/07_add_inventory_item.json
```

Command:

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H "mcp-session-id: $McpSessionId" `
  --data-binary "@curl_requests/07_add_inventory_item.json"
```

After running this command, confirm the item was added by reading the inventory again.

---


