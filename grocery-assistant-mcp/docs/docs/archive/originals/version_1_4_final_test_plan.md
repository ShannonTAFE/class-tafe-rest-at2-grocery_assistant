# Version 1.4 Final Test Plan — Fresh Empty Dataset

## Purpose

This test plan verifies Version 1.4 from a clean state.

It checks that the project can start with empty CSV files, seed inventory, run intake-only batch meal logging, run inventory-linked batch meal logging, and inspect all resulting resources.

The test is designed to catch accidental assumptions caused by existing local data.

---

## Preconditions

From the project root:

```powershell
pytest -q
```

Expected result:

```text
all tests pass
```

Also make sure no MCP server process is already running.

---

## Step 1 — Reset to a Fresh Empty Dataset

Copy this script into:

```text
scripts/reset_empty_dataset_v1_4.py
```

Then run:

```powershell
python scripts/reset_empty_dataset_v1_4.py
```

Expected result:

```text
All tracked CSVs are rewritten with headers only.
A timestamped backup is created under backups/.
```

The reset should affect:

```text
user_inventory.csv
user_intake_history.csv
user_intake_items.csv
user_inventory_consumption.csv
user_food_waste.csv
```

---

## Step 2 — Run Full Test Suite Again

After the clean reset, run:

```powershell
pytest -q
```

Expected result:

```text
all tests pass
```

This confirms the test suite does not depend on existing real CSV contents.

---

## Step 3 — Start Streamable HTTP Server

Open terminal 1:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected output:

```text
Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal open.

---

## Step 4 — Run Curl Workflow

Open terminal 2.

Create a response folder:

```powershell
New-Item -ItemType Directory -Force curl_responses | Out-Null
```

Initialize the MCP session:

```powershell
curl.exe -i -s -X POST "http://127.0.0.1:8000/mcp" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  --data-binary "@docs/curl_requests/v1_4/00_initialize.json" `
  -D "curl_responses/00_initialize_headers.txt" `
  -o "curl_responses/00_initialize_body.txt"
```

Capture the session ID:

```powershell
$SessionId = (Select-String -Path ".\curl_responses\00_initialize_headers.txt" -Pattern "^mcp-session-id:\s*(.+)$").Matches[0].Groups[1].Value.Trim()
$SessionId
```

Send the initialized notification:

```powershell
curl.exe -s -X POST "http://127.0.0.1:8000/mcp" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -H "mcp-session-id: $SessionId" `
  --data-binary "@docs/curl_requests/v1_4/01_initialized.json" `
  -o "curl_responses/01_initialized_response.txt"
```

Define a helper function:

```powershell
function Invoke-McpRequest {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FileName
    )

    $RequestPath = "docs/curl_requests/v1_4/$FileName.json"
    $ResponsePath = "curl_responses/$FileName.response.txt"

    curl.exe -s -X POST "http://127.0.0.1:8000/mcp" `
      -H "Content-Type: application/json" `
      -H "Accept: application/json, text/event-stream" `
      -H "mcp-session-id: $SessionId" `
      --data-binary "@$RequestPath" `
      -o $ResponsePath

    Get-Content $ResponsePath
}
```

Run the workflow:

```powershell
Invoke-McpRequest "02_tools_list"
Invoke-McpRequest "03_resources_list"
Invoke-McpRequest "04_read_inventory_empty"
Invoke-McpRequest "05_add_inventory_spaghetti"
Invoke-McpRequest "06_add_inventory_beef_mince"
Invoke-McpRequest "07_add_inventory_tomato_sauce"
Invoke-McpRequest "08_read_inventory_after_seed"
Invoke-McpRequest "09_add_meal_with_items_intake_only"
Invoke-McpRequest "10_read_intake_history_after_1_4b"
Invoke-McpRequest "11_read_intake_items_after_1_4b"
Invoke-McpRequest "12_add_meal_with_inventory_items"
Invoke-McpRequest "13_read_inventory_after_1_4c"
Invoke-McpRequest "14_read_inventory_consumption_after_1_4c"
Invoke-McpRequest "15_read_intake_history_final"
Invoke-McpRequest "16_read_intake_items_final"
Invoke-McpRequest "17_read_food_waste_final"
```

---

## Expected End State

After the full curl workflow:

```text
user_inventory.csv:
    3 seeded inventory rows
    inv_001, inv_002, and inv_003 reduced by the Version 1.4C call

user_intake_history.csv:
    2 parent meal rows
    intake_001 from add_meal_with_items
    intake_002 from add_meal_with_inventory_items

user_intake_items.csv:
    child rows from both batch workflows

user_inventory_consumption.csv:
    3 linked consumption rows from add_meal_with_inventory_items

user_food_waste.csv:
    empty except headers
```

Expected Version 1.4B result:

```text
add_meal_with_items creates parent + child intake rows only.
Inventory and consumption are unchanged by the 1.4B call.
```

Expected Version 1.4C result:

```text
add_meal_with_inventory_items creates parent + child intake rows, updates selected inventory rows, and creates linked consumption records.
```

---

## Final Closeout Commands

After verification:

```powershell
git status
pytest -q
git add docs/ scripts/
git commit -m "docs: close out Version 1.4"
```
