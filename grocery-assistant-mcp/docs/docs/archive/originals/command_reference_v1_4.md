# Command Reference — Version 1.4

This command reference matches the current documentation folder structure:

```text
C:.
├───version_1_4
│   │   command_reference_v1_4.md
│   │   mcp_testing_guide_v1_4.md
│   │
│   ├───curl_requests
│   │   │   00_initialize.json
│   │   │   01_initialized_notification.json
│   │   │   02_list_tools.json
│   │   │   03_list_resources.json
│   │   │   README.md
│   │   │
│   │   ├───intake
│   │   ├───inventory
│   │   ├───resources
│   │   └───validation
│   │
│   └───curl_responses
```

The commands below assume you are running PowerShell from the folder that contains:

```text
version_1_4/
```

In this project, that is usually the `docs` folder.

---

## Run Tests

These commands should be run from the project root, not from the docs folder.

Run the full test suite:

```powershell
pytest -q
```

Run Version 1.4B batch meal tests:

```powershell
pytest tests/test_batch_meal_service.py -q
```

Run Version 1.4C batch inventory meal tests:

```powershell
pytest tests/test_batch_inventory_meal_service.py -q
```

Run MCP tool registration tests:

```powershell
pytest tests/test_mcp_tool_registration.py -q
```

Run MCP resource registration tests:

```powershell
pytest tests/test_mcp_resource_registration.py -q
```

---

## Start Streamable HTTP Server

From the project root:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected MCP endpoint:

```text
http://127.0.0.1:8000/mcp
```

The root URL may return:

```text
404 Not Found
```

This is expected. The MCP server is exposed at `/mcp`, not `/`.

---

## Open MCP Inspector

In a second terminal:

```powershell
npx @modelcontextprotocol/inspector
```

Use:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
```

---

# Curl Testing Setup

From the folder that contains `version_1_4/`, set the request and response paths:

```powershell
$RequestRoot = "version_1_4/curl_requests"
$ResponseRoot = "version_1_4/curl_responses"
New-Item -ItemType Directory -Force $ResponseRoot | Out-Null
```

Confirm the request files are available:

```powershell
Test-Path "$RequestRoot/00_initialize.json"
Test-Path "$RequestRoot/02_list_tools.json"
```

Both should return:

```text
True
```

---

# Why Responses Are Not Direct JSON

MCP Streamable HTTP responses are returned as server-sent event style text.

A raw response may look like this:

```text
event: message
data: {"jsonrpc":"2.0","id":2,"result":{"tools":[...]}}
```

The actual JSON is the content after:

```text
data:
```

Because of this, saving the direct curl output as `.json` is not ideal. The better workflow is:

```text
1. Save raw response temporarily as *.raw.txt
2. Extract the data: JSON payload
3. Save the extracted payload as a clean *.json file
4. Inspect the *.json file in VS Code or pretty-print it
```

---

# Initialize MCP Curl Session

Send the initialize request:

```powershell
curl.exe -i -s -X POST "http://127.0.0.1:8000/mcp" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  --data-binary "@$RequestRoot/00_initialize.json" `
  -D "$ResponseRoot/00_initialize_headers.txt" `
  -o "$ResponseRoot/00_initialize_raw.txt"
```

Extract the MCP session ID:

```powershell
$SessionId = (Select-String -Path "$ResponseRoot/00_initialize_headers.txt" -Pattern "^mcp-session-id:\s*(.+)$").Matches[0].Groups[1].Value.Trim()
$SessionId
```

Expected result:

```text
A session id should print in the terminal.
```

---

## Send Initialized Notification

```powershell
curl.exe -s -X POST "http://127.0.0.1:8000/mcp" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -H "mcp-session-id: $SessionId" `
  --data-binary "@$RequestRoot/01_initialized_notification.json" `
  -o "$ResponseRoot/01_initialized_notification_raw.txt"
```

The initialized notification may not produce a meaningful JSON body. This is normal.

---

# Main Helper: Save Responses as JSON Files

Paste this helper directly into PowerShell after initializing the session.

```powershell
function Invoke-McpRequestJson {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RequestFile
    )

    $ResponseName = ($RequestFile -replace "[\\/]", "_") -replace "\.json$", ""
    $RequestPath = Join-Path $RequestRoot $RequestFile
    $RawPath = Join-Path $ResponseRoot "$ResponseName.raw.txt"
    $JsonPath = Join-Path $ResponseRoot "$ResponseName.json"

    if (-not (Test-Path $RequestPath)) {
        throw "Request file not found: $RequestPath"
    }

    curl.exe -s -X POST "http://127.0.0.1:8000/mcp" `
      -H "Content-Type: application/json" `
      -H "Accept: application/json, text/event-stream" `
      -H "mcp-session-id: $SessionId" `
      --data-binary "@$RequestPath" `
      -o $RawPath

    $Raw = Get-Content $RawPath -Raw

    $Json = ($Raw -split "`n" |
        Where-Object { $_ -match "^\s*data:" } |
        Select-Object -First 1) -replace "^\s*data:\s*", ""

    if ([string]::IsNullOrWhiteSpace($Json)) {
        Write-Host "No JSON data line found. Raw response saved to: $RawPath"
        return
    }

    $Json | ConvertFrom-Json | ConvertTo-Json -Depth 100 | Out-File $JsonPath -Encoding utf8

    Write-Host "Saved JSON response to: $JsonPath"
}
```

Example:

```powershell
Invoke-McpRequestJson "02_list_tools.json"
```

This creates:

```text
version_1_4/curl_responses/02_list_tools.raw.txt
version_1_4/curl_responses/02_list_tools.json
```

Use the `.json` file for readable inspection.

---

# Optional: Pretty Print a Saved JSON Response in Terminal

```powershell
Get-Content "version_1_4/curl_responses/02_list_tools.json" -Raw
```

Or parse and print again:

```powershell
Get-Content "version_1_4/curl_responses/02_list_tools.json" -Raw |
  ConvertFrom-Json |
  ConvertTo-Json -Depth 100
```

---

# Optional: Show Only Tool Names

After running:

```powershell
Invoke-McpRequestJson "02_list_tools.json"
```

Use:

```powershell
$ToolsResponse = Get-Content "$ResponseRoot/02_list_tools.json" -Raw | ConvertFrom-Json
$ToolsResponse.result.tools.name
```

This prints only the tool names.

---

# Optional: Show Tools as a Table

```powershell
$ToolsResponse = Get-Content "$ResponseRoot/02_list_tools.json" -Raw | ConvertFrom-Json

$ToolsResponse.result.tools |
  Select-Object name, description |
  Format-Table -Wrap -AutoSize
```

---

# Optional: Show Resources as a Table

After running:

```powershell
Invoke-McpRequestJson "03_list_resources.json"
```

Use:

```powershell
$ResourcesResponse = Get-Content "$ResponseRoot/03_list_resources.json" -Raw | ConvertFrom-Json

$ResourcesResponse.result.resources |
  Select-Object uri, name, mimeType, description |
  Format-Table -Wrap -AutoSize
```

If your response structure differs, inspect the saved JSON file first.

---

# Basic MCP Inspection

List registered tools:

```powershell
Invoke-McpRequestJson "02_list_tools.json"
```

List registered resources:

```powershell
Invoke-McpRequestJson "03_list_resources.json"
```

These two requests should be run before the workflow tests to confirm that the MCP server has loaded the expected Version 1.4 tools and resources.

---

# Full Version 1.4 Clean Dataset Curl Workflow

This workflow assumes the CSV files have been reset to headers only.

## 1. Inspect MCP Server

```powershell
Invoke-McpRequestJson "02_list_tools.json"
Invoke-McpRequestJson "03_list_resources.json"
```

Expected:

```text
The server should return the currently registered MCP tools and resources.
```

---

## 2. Seed Inventory Items

```powershell
Invoke-McpRequestJson "inventory/10_add_inventory_spaghetti.json"
Invoke-McpRequestJson "inventory/11_add_inventory_beef_mince.json"
Invoke-McpRequestJson "inventory/12_add_inventory_tomato_sauce.json"
```

Expected:

```text
Three inventory records should be created.
```

From a fresh empty dataset, expected IDs are usually:

```text
inv_001 = Spaghetti
inv_002 = Beef mince
inv_003 = Tomato pasta sauce
```

Still verify this from the returned responses before running update requests.

---

## 3. Search Inventory

```powershell
Invoke-McpRequestJson "inventory/13_search_inventory_all.json"
Invoke-McpRequestJson "inventory/14_search_inventory_protein.json"
```

Expected:

```text
13_search_inventory_all should return all seeded inventory items.
14_search_inventory_protein should return Beef mince.
```

---

## 4. Update Inventory

```powershell
Invoke-McpRequestJson "inventory/15_update_inventory_beef_mince_low.json"
```

Expected:

```text
Beef mince should update to quantity 100, servings_remaining 1, and stock_status low.
```

Then confirm:

```powershell
Invoke-McpRequestJson "inventory/16_search_inventory_low_stock.json"
```

---

## 5. Add Intake Entry

```powershell
Invoke-McpRequestJson "intake/20_add_intake_spaghetti_bolognese.json"
```

Expected:

```text
A dinner intake entry should be created for Spaghetti bolognese on 2026-05-18.
```

---

## 6. Search Intake

```powershell
Invoke-McpRequestJson "intake/21_search_intake_by_date.json"
Invoke-McpRequestJson "intake/22_search_intake_spaghetti.json"
```

Expected:

```text
The date search should return the 2026-05-18 dinner entry.
The spaghetti search should return the matching spaghetti bolognese intake record.
```

---

## 7. Read MCP Resources

```powershell
Invoke-McpRequestJson "resources/30_read_inventory_resource.json"
Invoke-McpRequestJson "resources/31_read_intake_history_resource.json"
Invoke-McpRequestJson "resources/32_read_intake_items_resource.json"
```

Expected:

```text
The inventory resource should show the seeded inventory records.
The intake history resource should show the added spaghetti bolognese meal.
The intake items resource may be empty unless the current intake tool creates component rows.
```

---

## 8. Run Validation Tests

These requests should fail safely with validation errors.

```powershell
Invoke-McpRequestJson "validation/40_add_inventory_missing_food_item.json"
Invoke-McpRequestJson "validation/41_add_inventory_negative_quantity.json"
Invoke-McpRequestJson "validation/42_update_inventory_unknown_id.json"
Invoke-McpRequestJson "validation/43_add_intake_invalid_date.json"
```

Expected:

```text
Each request should return an MCP error response or tool-level validation error.
The server should remain running.
The CSV files should not be corrupted.
```

---

# Full Copy-Paste Workflow

After initialization and notification, this is the full workflow:

```powershell
Invoke-McpRequestJson "02_list_tools.json"
Invoke-McpRequestJson "03_list_resources.json"

Invoke-McpRequestJson "inventory/10_add_inventory_spaghetti.json"
Invoke-McpRequestJson "inventory/11_add_inventory_beef_mince.json"
Invoke-McpRequestJson "inventory/12_add_inventory_tomato_sauce.json"

Invoke-McpRequestJson "inventory/13_search_inventory_all.json"
Invoke-McpRequestJson "inventory/14_search_inventory_protein.json"

Invoke-McpRequestJson "inventory/15_update_inventory_beef_mince_low.json"
Invoke-McpRequestJson "inventory/16_search_inventory_low_stock.json"

Invoke-McpRequestJson "intake/20_add_intake_spaghetti_bolognese.json"
Invoke-McpRequestJson "intake/21_search_intake_by_date.json"
Invoke-McpRequestJson "intake/22_search_intake_spaghetti.json"

Invoke-McpRequestJson "resources/30_read_inventory_resource.json"
Invoke-McpRequestJson "resources/31_read_intake_history_resource.json"
Invoke-McpRequestJson "resources/32_read_intake_items_resource.json"

Invoke-McpRequestJson "validation/40_add_inventory_missing_food_item.json"
Invoke-McpRequestJson "validation/41_add_inventory_negative_quantity.json"
Invoke-McpRequestJson "validation/42_update_inventory_unknown_id.json"
Invoke-McpRequestJson "validation/43_add_intake_invalid_date.json"
```

---

# Response Files Created

For each request, the helper creates:

```text
*.raw.txt
*.json
```

Example:

```text
version_1_4/curl_responses/02_list_tools.raw.txt
version_1_4/curl_responses/02_list_tools.json
```

Use the `.json` files for review.

The `.raw.txt` files are kept only for debugging the underlying MCP streamable HTTP response.

---

# Notes About Version 1.4 Clean Dataset Testing

The Version 1.4 curl workflow is designed to run from CSV files that contain only header rows.

This means the workflow should create its own test records through MCP tools rather than relying on old manually seeded records.

The update request:

```text
inventory/15_update_inventory_beef_mince_low.json
```

currently assumes:

```text
stock_id = inv_002
```

That should be correct if the workflow is run from a fully empty dataset and the first three inventory add requests are run in order.

If the dataset is not empty, update the `stock_id` in that request file to match the actual Beef mince record returned by search.

---

# Troubleshooting

## PowerShell cannot find a request file

Check that you are running commands from the folder that contains:

```text
version_1_4/
```

Then confirm the request root:

```powershell
Test-Path "version_1_4/curl_requests/00_initialize.json"
Test-Path "version_1_4/curl_requests/02_list_tools.json"
```

Both should return:

```text
True
```

If they return `False`, change `$RequestRoot` to match your current location.

---

## Session ID is blank

Re-run:

```powershell
Get-Content "$ResponseRoot/00_initialize_headers.txt"
```

Look for:

```text
mcp-session-id:
```

If it is missing, the initialize request likely failed.

---

## JSON response file was not created

Check the raw response:

```powershell
Get-Content "$ResponseRoot/02_list_tools.raw.txt" -Raw
```

Look for a line starting with:

```text
data:
```

If there is no `data:` line, the server may have returned an error, the session may be missing, or the request may have failed before MCP produced a JSON-RPC response.

---

## Root URL gives 404

This is expected:

```text
http://127.0.0.1:8000/
```

The MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

---

## GET /mcp gives 406 Not Acceptable

This can happen when opening the MCP endpoint directly in a browser.

Use POST requests with the required headers:

```text
Content-Type: application/json
Accept: application/json, text/event-stream
```

---

## Update inventory fails with unknown ID

Check the actual generated IDs:

```powershell
Invoke-McpRequestJson "inventory/13_search_inventory_all.json"
```

Then edit:

```text
version_1_4/curl_requests/inventory/15_update_inventory_beef_mince_low.json
```

to use the correct `stock_id`.

---

## Resource read fails

Run:

```powershell
Invoke-McpRequestJson "03_list_resources.json"
```

Check the actual resource URIs returned by your server.

Then update the files inside:

```text
version_1_4/curl_requests/resources/
```

to match your current registered resource names.
