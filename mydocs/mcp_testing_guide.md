# MCP Testing Guide

## Purpose

This guide documents the manual testing workflow for the Grocery Assistant MCP project.

It covers two main testing methods:

1. MCP Inspector
2. curl against the streamable HTTP server

Unit tests should still be run with `pytest`. This guide focuses on checking the actual MCP interface exposed to a client.

---

# Testing Layers

The project can be tested at several levels:

```text
Service tests:
Python functions directly read/write CSV data.

MCP registration tests:
Resources, tools, and prompts are registered with the MCP server.

MCP Inspector tests:
A visual/manual MCP client calls tools and resources.

Curl tests:
Raw MCP JSON-RPC requests are sent to the streamable HTTP endpoint.
```

Version 1.1 should pass all relevant layers before being considered complete.

---

# MCP Inspector — Stdio Testing

Run from the project root:

```powershell
npx @modelcontextprotocol/inspector .\.venv\Scripts\python.exe -m grocery_assistant_mcp.stdio_server
```

Suggested manual test order:

```text
1. Connect to the server.
2. List resources.
3. Read grocery://inventory.
4. Read grocery://intake/history.
5. Read grocery://intake/items.
6. Read grocery://food-waste.
7. List tools.
8. Call search_inventory.
9. Call add_inventory_item.
10. Call update_inventory_item.
11. Call remove_inventory_item with a non-waste reason.
12. Call remove_inventory_item with a waste reason.
13. Call add_intake_entry.
14. Call add_intake_item.
15. Confirm invalid input produces clear errors.
```

---

# MCP Inspector — Streamable HTTP Testing

Start the HTTP server in one terminal:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Open MCP Inspector:

```powershell
npx @modelcontextprotocol/inspector
```

Use:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
```

Then repeat the same manual test order used for stdio.

---

# Curl Testing Workflow

## 1. Start the Streamable HTTP Server

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Endpoint:

```text
http://127.0.0.1:8000/mcp
```

Browser responses such as `404 Not Found` for `/` or `406 Not Acceptable` for `/mcp` are expected. The `/mcp` endpoint expects MCP JSON-RPC requests with specific headers.

---

## 2. Set PowerShell Variables

```powershell
$BaseUrl = "http://127.0.0.1:8000"
$McpUrl = "$BaseUrl/mcp"

$ContentType = "Content-Type: application/json"
$Accept = "Accept: application/json, text/event-stream"
$ProtocolVersion = "MCP-Protocol-Version: 2025-06-18"
```

---

## 3. Initialize the Session

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  --data-binary "@curl_requests/01_initialize.json"
```

Copy the returned `mcp-session-id` header:

```powershell
$McpSessionId = "paste-session-id-here"
```

---

## 4. Send Initialized Notification

```powershell
curl.exe -i -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H "mcp-session-id: $McpSessionId" `
  --data-binary "@curl_requests/02_initialized_notification.json"
```

---

## 5. Create a Helper Function

After the session ID is set, define:

```powershell
function Invoke-McpRequest {
    param (
        [Parameter(Mandatory=$true)]
        [string]$RequestFile
    )

    curl.exe -i -X POST $McpUrl `
      -H $ContentType `
      -H $Accept `
      -H "mcp-session-id: $McpSessionId" `
      --data-binary "@$RequestFile"
}
```

Then run requests like:

```powershell
Invoke-McpRequest "curl_requests/03_resources_list.json"
Invoke-McpRequest "curl_requests/04_read_inventory.json"
Invoke-McpRequest "curl_requests/05_tools_list.json"
```

---

# Suggested Curl Request Files

```text
curl_requests/01_initialize.json
curl_requests/02_initialized_notification.json
curl_requests/03_resources_list.json
curl_requests/04_read_inventory.json
curl_requests/05_tools_list.json
curl_requests/06_prompts_list.json
curl_requests/07_add_inventory_item.json
curl_requests/08_update_inventory_item.json
curl_requests/09_remove_inventory_item.json
curl_requests/10_add_intake_entry.json
curl_requests/11_add_intake_item.json
```

---

# Example JSON-RPC Request Bodies

## List Resources

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/list",
  "params": {}
}
```

## Read Inventory

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/read",
  "params": {
    "uri": "grocery://inventory"
  }
}
```

## List Tools

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/list",
  "params": {}
}
```

## Add Inventory Item

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "add_inventory_item",
    "arguments": {
      "food_item": "Greek yoghurt",
      "brand": "Example Brand",
      "category": "dairy",
      "location": "fridge",
      "quantity": 1,
      "unit": "tub",
      "servings_remaining": 5,
      "stock_status": "ok",
      "expiry_date": "2026-06-01",
      "notes": "Added during V1.1 testing"
    }
  }
}
```

## Add Intake Entry

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/call",
  "params": {
    "name": "add_intake_entry",
    "arguments": {
      "date": "2026-05-16",
      "time": "18:30",
      "meal_type": "dinner",
      "meal_name": "Spaghetti bolognese",
      "meal_description": "Home cooked batch meal",
      "source": "home",
      "amount_eaten": "1 large bowl",
      "portion_confidence": "medium",
      "nutrition_confidence": "medium",
      "was_finished": "yes",
      "leftovers_created": "yes",
      "notes": "V1.1 intake test"
    }
  }
}
```

## Add Intake Item

```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "method": "tools/call",
  "params": {
    "name": "add_intake_item",
    "arguments": {
      "intake_id": "intake_001",
      "food_item": "Spaghetti",
      "brand": "San Remo",
      "category": "pantry",
      "source": "home",
      "stock_id": "",
      "amount_eaten": "1 serve",
      "servings_used": 1,
      "portion_confidence": "medium",
      "nutrition_confidence": "medium",
      "notes": "Component of spaghetti bolognese"
    }
  }
}
```

---

# JSON-RPC ID vs MCP Session ID

These are different concepts.

```text
JSON-RPC id:
A request/response identifier inside the JSON body.

mcp-session-id:
A server-issued session identifier returned in the HTTP headers.
```

Changing the JSON-RPC ID does not change the MCP session.

Restarting the server usually means you need a new MCP session ID.

---

# Common Issues

## Browser Shows 404 or 406

This is expected for normal browser requests.

The MCP endpoint is not a normal webpage. It expects JSON-RPC requests and MCP headers.

---

## File Not Found

Check current directory:

```powershell
pwd
```

Check request files:

```powershell
dir curl_requests
```

---

## Invalid JSON Parse Error

Make sure request files contain valid JSON only. Do not include comments inside JSON files.

Good pattern:

```powershell
--data-binary "@curl_requests/03_resources_list.json"
```

---

## Empty Session Variable

Check that `$McpSessionId` is set:

```powershell
$McpSessionId
```

If it is empty, rerun initialize and copy the returned `mcp-session-id`.

---

# Recommended V1.1 Manual Test Sequence

```powershell
Invoke-McpRequest "curl_requests/03_resources_list.json"
Invoke-McpRequest "curl_requests/04_read_inventory.json"
Invoke-McpRequest "curl_requests/05_tools_list.json"
Invoke-McpRequest "curl_requests/06_prompts_list.json"
Invoke-McpRequest "curl_requests/07_add_inventory_item.json"
Invoke-McpRequest "curl_requests/04_read_inventory.json"
```

This confirms the basic read/write/read cycle.
