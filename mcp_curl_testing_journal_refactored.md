# MCP Curl Testing Journal

This journal documents a clean PowerShell-first workflow for testing the Grocery Assistant MCP Streamable HTTP server with curl.

The goal is to keep the learning aspect visible while reducing repeated typing:

- clearly see the MCP URL, headers, and request files
- send JSON-RPC request bodies from `.json` files
- automatically capture the `mcp-session-id`
- reuse the same session ID through a helper function
- keep raw curl output visible for learning and debugging

---

## 1. Project Root

Run curl commands from the project root so relative request-file paths work correctly.

```powershell
cd C:\Users\shann\TafeLocal\rest-at2\grocery-assistant-mcp
```

Request files are stored in:

```text
curl_requests/
```

Current request files:

```text
curl_requests/01_initialize.json
curl_requests/02_initialized_notification.json
curl_requests/03_resources_list.json
curl_requests/04_read_inventory.json
curl_requests/05_tools_list.json
curl_requests/06_prompts_list.json
curl_requests/07_add_inventory_item.json
```

---

## 2. Start the Streamable HTTP Server

Open one terminal for the server and run:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

The MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

Browser checks may show:

```text
GET /      -> 404 Not Found
GET /mcp   -> 406 Not Acceptable
```

This is expected. The `/mcp` endpoint expects MCP JSON-RPC requests, not normal browser page requests.

---

## 3. Set Reusable PowerShell Variables

Open a second terminal for curl commands and run:

```powershell
$BaseUrl = "http://127.0.0.1:8000"
$McpUrl = "$BaseUrl/mcp"

$ContentType = "Content-Type: application/json"
$Accept = "Accept: application/json, text/event-stream"
$ProtocolVersion = "MCP-Protocol-Version: 2025-06-18"
```

These variables make the curl commands easier to read.

For this local project, no authorization header is needed unless authentication is added later.

Avoid saving real bearer tokens in GitHub, README files, or journals.

---

## 4. Initialize and Automatically Capture the Session ID

The initialize request starts the MCP handshake.

Request file:

```text
curl_requests/01_initialize.json
```

Expected file content:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "grocery-curl-client",
      "version": "1.0.0"
    }
  }
}
```

Run this command to send the request and capture the returned `mcp-session-id` header:

```powershell
$InitResponse = curl.exe -s -D - -o NUL -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H $ProtocolVersion `
  --data-binary "@curl_requests/01_initialize.json"

$McpSessionId = ($InitResponse | Select-String -Pattern "^mcp-session-id:" | ForEach-Object {
    $_.ToString().Split(":", 2)[1].Trim()
})

Write-Host "MCP Session ID: $McpSessionId"
```

What this does:

```text
-s             hides curl progress output
-D -           prints response headers to the terminal stream
-o NUL         discards the response body for this session-capture step
-X POST        sends a POST request
-H             adds required headers
--data-binary  sends the JSON body from the request file
```

The important output is:

```text
MCP Session ID: <session-id-value>
```

Example:

```text
MCP Session ID: 7ab88075d6744da99d21802e73b6b74a
```

---

## 5. Session ID Mental Model

The `mcp-session-id` is not the same as the JSON-RPC `id`.

```text
JSON-RPC id:
- inside the JSON body
- changes for each request
- matches a response to a request

mcp-session-id:
- sent as an HTTP header
- stays the same during the initialized MCP session
- tells the server this request belongs to the already-initialized client
```

Example:

```text
Request body id: 3
HTTP header mcp-session-id: 7ab88075d6744da99d21802e73b6b74a
```

The body ID identifies the request.

The session ID identifies the MCP session.

---

## 6. Create a Reusable MCP Curl Function

After `$McpSessionId` has been captured, define this helper:

```powershell
function Invoke-McpCurl {
    param (
        [string]$RequestFile
    )

    curl.exe -i -X POST $McpUrl `
      -H $ContentType `
      -H $Accept `
      -H $ProtocolVersion `
      -H "mcp-session-id: $McpSessionId" `
      --data-binary "@$RequestFile"
}
```

Now requests are short and readable:

```powershell
Invoke-McpCurl "curl_requests/03_resources_list.json"
```

This still clearly shows:

```text
which request file is being sent
```

but avoids repeating the URL, headers, and session ID every time.

---

## 7. Optional Helper: Show Current MCP Settings

This is useful for checking that the variables are set correctly:

```powershell
function Show-McpCurlSettings {
    Write-Host "MCP URL:        $McpUrl"
    Write-Host "Session ID:     $McpSessionId"
    Write-Host "Content-Type:   $ContentType"
    Write-Host "Accept:         $Accept"
    Write-Host "Protocol:       $ProtocolVersion"
}
```

Run:

```powershell
Show-McpCurlSettings
```

---

## 8. Send Initialized Notification

After initialization, send the initialized notification.

Request file:

```text
curl_requests/02_initialized_notification.json
```

Expected file content:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

Run:

```powershell
Invoke-McpCurl "curl_requests/02_initialized_notification.json"
```

Purpose:

```text
Completes the MCP initialization lifecycle.
```

This notification has no JSON-RPC `id` because it is not asking for a response result.

---

## 9. List Resources

Request file:

```text
curl_requests/03_resources_list.json
```

Expected file content:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/list"
}
```

Run:

```powershell
Invoke-McpCurl "curl_requests/03_resources_list.json"
```

Expected resources:

```text
grocery://inventory
grocery://intake-history
grocery://intake-items
```

This confirms that MCP resource registration is working.

---

## 10. Read Inventory

Request file:

```text
curl_requests/04_read_inventory.json
```

Expected file content:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/read",
  "params": {
    "uri": "grocery://inventory"
  }
}
```

Run:

```powershell
Invoke-McpCurl "curl_requests/04_read_inventory.json"
```

This tests the full read path:

```text
curl request
→ Streamable HTTP MCP endpoint
→ resources/read
→ grocery://inventory
→ CSV-backed inventory data
→ JSON-RPC response
```

---

## 11. List Tools

Request file:

```text
curl_requests/05_tools_list.json
```

Expected file content:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/list"
}
```

Run:

```powershell
Invoke-McpCurl "curl_requests/05_tools_list.json"
```

Current expected tools include:

```text
search_inventory
add_inventory_item
get_recent_intake
get_daily_intake_summary
```

This confirms that MCP tool registration is working.

---

## 12. List Prompts

Request file:

```text
curl_requests/06_prompts_list.json
```

Expected file content:

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "prompts/list"
}
```

Run:

```powershell
Invoke-McpCurl "curl_requests/06_prompts_list.json"
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

## 13. Test Add Inventory Item

Request file:

```text
curl_requests/07_add_inventory_item.json
```

Expected file content:

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "add_inventory_item",
    "arguments": {
      "food_item": "Rolled oats",
      "brand": "Uncle Tobys",
      "category": "pantry",
      "location": "cupboard",
      "quantity": 1,
      "unit": "bag",
      "servings_remaining": 10,
      "stock_status": "ok",
      "expiry_date": "2026-12-01",
      "notes": "Added during Version 1.1 curl test"
    }
  }
}
```

Run:

```powershell
Invoke-McpCurl "curl_requests/07_add_inventory_item.json"
```

Then read inventory again:

```powershell
Invoke-McpCurl "curl_requests/04_read_inventory.json"
```

Look for the newly added item in the response.

Also check that a backup file was created before the write if backup logic has been added.

---

## 14. Cleaner Inventory Output

Raw Streamable HTTP output may look like this:

```text
event: message
data: {"jsonrpc":"2.0","id":3,"result":{...}}
```

The useful JSON-RPC response is inside the `data:` line.

For resource reads, the actual resource text is usually inside:

```text
result.contents[0].text
```

To display inventory as a table in PowerShell:

```powershell
$response = curl.exe -s -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H $ProtocolVersion `
  -H "mcp-session-id: $McpSessionId" `
  --data-binary "@curl_requests/04_read_inventory.json"

$jsonLine = ($response | Select-String "^data: ").ToString().Replace("data: ", "")
$mcpJson = $jsonLine | ConvertFrom-Json
$inventoryText = $mcpJson.result.contents[0].text
$inventory = $inventoryText | ConvertFrom-Json
$inventory | Format-Table stock_id, food_item, quantity, unit, servings_remaining, stock_status, expiry_date
```

This keeps curl testing visible but makes the returned inventory easier to inspect.

---

## 15. Full Test Sequence

Use this sequence for a fresh Streamable HTTP test session.

```powershell
cd C:\Users\shann\TafeLocal\rest-at2\grocery-assistant-mcp

$BaseUrl = "http://127.0.0.1:8000"
$McpUrl = "$BaseUrl/mcp"
$ContentType = "Content-Type: application/json"
$Accept = "Accept: application/json, text/event-stream"
$ProtocolVersion = "MCP-Protocol-Version: 2025-06-18"

$InitResponse = curl.exe -s -D - -o NUL -X POST $McpUrl `
  -H $ContentType `
  -H $Accept `
  -H $ProtocolVersion `
  --data-binary "@curl_requests/01_initialize.json"

$McpSessionId = ($InitResponse | Select-String -Pattern "^mcp-session-id:" | ForEach-Object {
    $_.ToString().Split(":", 2)[1].Trim()
})

Write-Host "MCP Session ID: $McpSessionId"

function Invoke-McpCurl {
    param (
        [string]$RequestFile
    )

    curl.exe -i -X POST $McpUrl `
      -H $ContentType `
      -H $Accept `
      -H $ProtocolVersion `
      -H "mcp-session-id: $McpSessionId" `
      --data-binary "@$RequestFile"
}

Invoke-McpCurl "curl_requests/02_initialized_notification.json"
Invoke-McpCurl "curl_requests/03_resources_list.json"
Invoke-McpCurl "curl_requests/04_read_inventory.json"
Invoke-McpCurl "curl_requests/05_tools_list.json"
Invoke-McpCurl "curl_requests/06_prompts_list.json"
Invoke-McpCurl "curl_requests/07_add_inventory_item.json"
Invoke-McpCurl "curl_requests/08_add_inventory_missing_food_item.json"
Invoke-McpCurl "curl_requests/09_add_inventory_invalid_date.json"
Invoke-McpCurl "curl_requests/10_add_inventory_negative_quantity.json"
Invoke-McpCurl "curl_requests/11_add_yoghurt.json"
Invoke-McpCurl "curl_requests/12_remove_yoghurt_expired.json"
Invoke-McpCurl "curl_requests/13_remove_item_used_up.json"
```

---

## 16. Optional: Save Helpers as a Script

To avoid retyping the setup every time, save the variables and helper functions in:

```text
scripts/mcp_curl_helpers.ps1
```

Example file content:

```powershell
$BaseUrl = "http://127.0.0.1:8000"
$McpUrl = "$BaseUrl/mcp"
$ContentType = "Content-Type: application/json"
$Accept = "Accept: application/json, text/event-stream"
$ProtocolVersion = "MCP-Protocol-Version: 2025-06-18"

function Initialize-McpCurl {
    $InitResponse = curl.exe -s -D - -o NUL -X POST $McpUrl `
      -H $ContentType `
      -H $Accept `
      -H $ProtocolVersion `
      --data-binary "@curl_requests/01_initialize.json"

    $script:McpSessionId = ($InitResponse | Select-String -Pattern "^mcp-session-id:" | ForEach-Object {
        $_.ToString().Split(":", 2)[1].Trim()
    })

    Write-Host "MCP Session ID: $script:McpSessionId"
}

function Invoke-McpCurl {
    param (
        [string]$RequestFile
    )

    curl.exe -i -X POST $McpUrl `
      -H $ContentType `
      -H $Accept `
      -H $ProtocolVersion `
      -H "mcp-session-id: $script:McpSessionId" `
      --data-binary "@$RequestFile"
}
```

Load it from the project root:

```powershell
. .\scripts\mcp_curl_helpers.ps1
```

Then run:

```powershell
Initialize-McpCurl
Invoke-McpCurl "curl_requests/02_initialized_notification.json"
Invoke-McpCurl "curl_requests/03_resources_list.json"
Invoke-McpCurl "curl_requests/04_read_inventory.json"
```

---

## 17. Bash Comparison

A bash version can use environment-style variables and command substitution:

```bash
BASE="http://localhost:8000"
MCP="$BASE/mcp"
ACCEPT="Accept: application/json, text/event-stream"
PROTO="MCP-Protocol-Version: 2025-06-18"

SESSION=$(curl -sD - -o /dev/null "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  --data-binary "@curl_requests/01_initialize.json" \
  | awk 'BEGIN{IGNORECASE=1} /^mcp-session-id:/ {sub(/\r$/,""); print $2}')

echo "SESSION=$SESSION"
```

This is the same idea as the PowerShell version:

```text
send initialize
read response headers
extract mcp-session-id
store it in a variable
reuse it in later requests
```

For this project, PowerShell is preferred because the development environment is Windows.

---

## 18. Common Issues

### File not found

Error:

```text
curl: Failed to open curl_requests/01_initialize.json
```

Cause:

```text
The current terminal folder does not contain the curl_requests directory, or the file does not exist.
```

Check location:

```powershell
pwd
```

Check request files:

```powershell
dir curl_requests
```

---

### Invalid JSON parse error

Error:

```text
Parse error: Expecting property name enclosed in double quotes
```

Cause:

```text
PowerShell/curl quoting changed the JSON body before sending it.
```

Fix:

```text
Use JSON request files and --data-binary instead of typing large JSON directly into the command.
```

---

### Old session ID after server restart

If the HTTP server is restarted, the old session ID should not be reused.

Start again from:

```text
01_initialize.json
```

Then recapture the new session ID.

---

### Empty session variable

If `$McpSessionId` is blank, initialization probably failed or the header was not captured.

Check the raw headers:

```powershell
$InitResponse
```

Look for:

```text
mcp-session-id: ...
```

---

## 19. Key Learning Summary

```text
initialize = starts the MCP handshake
notifications/initialized = completes setup
mcp-session-id = identifies the active MCP session
JSON-RPC id = identifies a specific request/response pair
--data-binary @file.json = sends the JSON request body from a file
Invoke-McpCurl = helper function to avoid repeating headers and session ID
```

The main testing pattern is:

```text
request JSON file
→ curl POST to /mcp
→ required headers
→ session ID header after initialization
→ JSON-RPC response inside data: line
```

