# Grocery Assistant MCP - Version 1

## Overview

Grocery Assistant MCP is a local Model Context Protocol server that exposes grocery inventory and food intake data to an MCP-compatible client.

Version 1 focuses on a small, testable, read-focused grocery assistant. The server allows a client or LLM assistant to inspect the user's current grocery inventory, review meal intake history, search inventory records, summarise daily intake, review recent intake, and use structured prompts for common grocery and nutrition workflows.

The current Version 1 implementation uses local CSV files as the data layer. These files are read through a core grocery service module, then exposed through MCP resources and tools. Prompts are also registered to guide the assistant through useful read-only workflows such as reviewing intake, summarising inventory, finding inventory items, and suggesting meals from available food.

Version 1 is intentionally limited to safe inspection and summary workflows. The current tools and prompts do not create, edit, or delete inventory or intake records. This keeps the first implementation easier to test and reduces the risk of accidental data changes while the MCP structure is being developed.

---

## Current Version 1 Capabilities

Version 1 currently supports:

* Reading the full grocery inventory
* Reading meal-level intake history
* Reading ingredient-level or component-level intake records
* Searching inventory by item name, brand notes, category, and location
* Getting recent intake records over a selected number of days
* Filtering recent intake by meal type
* Getting a daily intake summary for a selected date
* Calculating daily nutrition totals using item-level data when available
* Falling back to meal-level nutrition totals when item-level records are not available
* Tracking missing nutrition counts in daily summaries
* Using inventory prompts for stock summaries, item finding, and meal suggestions
* Using intake prompts for recent intake reviews, daily intake reviews, and next-meal suggestions

---

## Project Structure

The current Version 1 implementation is organised around separate MCP resource, tool, prompt, and service files.

```text
grocery-assistant-mcp/
│
├── src/
│   └── grocery_assistant_mcp/
│       │
│       ├── stdio_server.py
│       ├── streamable_http_server.py
│       │
│       ├── core/
│       │   └── grocery_service.py
│       │
│       ├── mcp_resources/
│       │   ├── inventory_resources.py
│       │   └── intake_resources.py
│       │
│       ├── mcp_tools/
│       │   ├── inventory_tools.py
│       │   └── intake_tools.py
│       │
│       ├── mcp_prompts/
│       │   ├── inventory_prompts.py
│       │   └── intake_prompts.py
│       │
│       └── utils/
│           └── paths.py
│
├── README.md
└── pyproject.toml
```

The core idea is that `grocery_service.py` handles the data-reading and filtering logic, while the MCP-specific files register that logic as resources, tools, and prompts.

---

## Data Layer

Version 1 uses local CSV files as the data source.

The core service reads these CSV files through configured paths:

```text
INVENTORY_PATH
INTAKE_HISTORY_PATH
INTAKE_ITEMS_PATH
```

These paths are imported from:

```text
grocery_assistant_mcp/utils/paths.py
```

The current data files are:

```text
user_inventory.csv
user_intake_history.csv
user_intake_items.csv
```

### Inventory Data

The inventory data stores current grocery stock. It supports inventory summaries, inventory searching, and meal suggestion workflows.

Expected inventory fields may include:

```text
stock_id, food_item, brand, category, location, quantity, unit, servings_remaining, stock_status, expiry_date, notes
```

### Intake History Data

The intake history data stores meal-level records. It supports recent intake review and daily intake summaries.

Expected intake history fields may include:

```text
intake_id, date, time, meal_type, meal_name, meal_description, source, amount_eaten, portion_confidence, total_calories_estimate, total_protein_g_estimate, total_carbs_g_estimate, total_fat_g_estimate, total_fibre_g_estimate, total_sugar_g_estimate, total_sodium_mg_estimate, nutrition_confidence, notes
```

### Intake Items Data

The intake items data stores ingredient-level or component-level food records linked to meal-level intake records.

Expected intake item fields may include:

```text
intake_item_id, intake_id, food_item, brand, category, source, stock_id, amount_eaten, servings_used, calories_estimate, protein_g_estimate, carbs_g_estimate, fat_g_estimate, fibre_g_estimate, sugar_g_estimate, sodium_mg_estimate, nutrition_confidence, notes
```

---

## Core Service

Main file:

```text
src/grocery_assistant_mcp/core/grocery_service.py
```

The core service contains the main data logic used by the MCP resources and tools.

Current service functions include:

```text
read_csv_file(path)
read_inventory()
read_intake_history()
read_intake_items()
df_to_records(df)
to_json(data)
list_inventory_items(category=None, low_stock_only=False)
find_inventory_item(search_term)
search_inventory(query="", category="", location="")
get_recent_intake(days_back=7, meal_type="")
get_daily_intake_summary(date)
```

### Service Behaviour

The service is designed to be safe for local testing:

* If a CSV file is missing, the service returns an empty DataFrame instead of crashing the MCP server.
* DataFrames are converted into lists of dictionaries for tool responses.
* Resource responses are converted into formatted JSON text.
* Inventory search supports broad text search and exact category/location filters.
* Recent intake is sorted newest first.
* Daily intake summaries combine meal-level and item-level data.

### Daily Intake Summary Logic

The daily intake summary uses a hybrid nutrition strategy:

1. It reads meal-level intake records for a selected date.
2. It finds matching item-level rows using `intake_id`.
3. If item-level rows exist for a meal, item-level nutrition totals are used.
4. If item-level rows do not exist, the function falls back to meal-level total nutrition columns.
5. The response includes nutrition totals, missing nutrition counts, meals, items, and which meals used item-level or meal-level totals.

This allows the system to support both detailed ingredient logs and quicker manual meal logs.

---

## MCP Resources

Resources expose read-only data to the MCP client.

### Inventory Resource

File:

```text
src/grocery_assistant_mcp/mcp_resources/inventory_resources.py
```

Registered resource:

```text
grocery://inventory
```

Purpose:

```text
Current grocery inventory.
```

This resource reads the inventory CSV and returns the records as formatted JSON.

---

### Intake Resources

File:

```text
src/grocery_assistant_mcp/mcp_resources/intake_resources.py
```

Registered resources:

```text
grocery://intake-history
grocery://intake-items
```

Purpose:

```text
grocery://intake-history
Meal-level food intake history.

grocery://intake-items
Ingredient-level or component-level intake records.
```

These resources expose the user's intake data as formatted JSON.

---

## MCP Tools

Tools expose specific callable operations to the MCP client.

The current Version 1 tools are read-only. They return filtered or summarised data, but they do not write to the CSV files.

### Inventory Tools

File:

```text
src/grocery_assistant_mcp/mcp_tools/inventory_tools.py
```

Registered tool:

```text
search_inventory(query="", category="", location="")
```

Purpose:

Search the user's grocery inventory by food name, brand notes, category, or location.

Input behaviour:

* `query` searches across food item, brand, and notes.
* `category` filters by exact category.
* `location` filters by exact storage location.

Example uses:

* Find all freezer items.
* Search for chicken.
* Find pantry carbohydrates.
* Check whether a specific item is available.

---

### Intake Tools

File:

```text
src/grocery_assistant_mcp/mcp_tools/intake_tools.py
```

Registered tools:

```text
get_recent_intake(days_back=7, meal_type="")
get_daily_intake_summary(date)
```

#### `get_recent_intake`

Returns recent food intake records from the user's intake history.

Input behaviour:

* `days_back` controls how many days back from today are included.
* `meal_type` can optionally filter by breakfast, lunch, dinner, snack, or another meal type.

Output:

* A list of recent intake history records, sorted newest first.

#### `get_daily_intake_summary`

Returns all logged meals, matching food items, and calculated nutrition totals for a selected date.

Input behaviour:

* `date` should be provided in `YYYY-MM-DD` format.

Output includes:

* date
* meal count
* item count
* meals
* items
* nutrition totals
* missing nutrition counts
* nutrition total source information
* meal IDs using item-level totals
* meal IDs using meal-level fallback totals

---

## MCP Prompts

Prompts provide reusable workflow guidance to the client or LLM assistant.

The current Version 1 prompts are read-only workflows. They may guide the assistant to read resources or call read-only tools, but they explicitly instruct the assistant not to log meals, modify intake records, update inventory, or create shopping lists unless the user explicitly asks for a draft list.

### Inventory Prompts

File:

```text
src/grocery_assistant_mcp/mcp_prompts/inventory_prompts.py
```

Registered prompts:

```text
summarise_inventory()
find_inventory_items()
suggest_meals_from_inventory()
```

#### `summarise_inventory`

Guides the assistant to read `grocery://inventory` and summarise available food in practical sections such as proteins, carbohydrates and grains, vegetables and fruit, pantry staples, fridge items, freezer items, and snacks or extras.

It also asks the assistant to identify low-stock or empty items, items that may need to be used soon, and useful meal opportunities from the current inventory.

#### `find_inventory_items`

Guides the assistant to use `search_inventory` when the user asks whether they have a specific food item, brand, category, or location-specific item.

The prompt asks the assistant to summarise matching items, quantities or servings remaining, stock status, location, expiry date, and useful ways the item could be used.

#### `suggest_meals_from_inventory`

Guides the assistant to suggest practical meals based on the user's current inventory.

The prompt prioritises available ingredients, large filling meals, high-protein options, fibre and vegetables, short shelf-life items, simple preparation, and batch-cook friendly meals.

---

### Intake Prompts

File:

```text
src/grocery_assistant_mcp/mcp_prompts/intake_prompts.py
```

Registered prompts:

```text
review_recent_intake(days_back=7, meal_type="")
review_daily_intake(date)
suggest_next_meal(date)
```

#### `review_recent_intake`

Guides the assistant to call `get_recent_intake` and review recent food intake.

The prompt asks the assistant to summarise meals eaten recently, repeated meals or patterns, likely protein sources, carbohydrate sources, fruit/vegetable/fibre patterns, variety, and practical suggestions for the next few meals.

#### `review_daily_intake`

Guides the assistant to call `get_daily_intake_summary` for a selected date.

The prompt asks the assistant to summarise meals eaten, item details, estimated nutrition totals, missing nutrition data, whether the day looks balanced, and what type of meal may fit next.

It also reminds the assistant that nutrition values are estimates and that missing nutrition data should be mentioned.

#### `suggest_next_meal`

Guides the assistant to suggest a suitable next meal for a selected date.

The prompt asks the assistant to use:

```text
get_daily_intake_summary(date)
grocery://inventory
search_inventory, if a specific ingredient, category, or location needs checking
```

The assistant should consider what the user has already eaten, current inventory, large filling healthy meals, protein balance, fibre and vegetable intake, simple preparation, avoiding unnecessary grocery purchases, and using food that may need to be used soon.

---

## Running the Server

Run commands should be executed from the project root.

### Stdio Server

File path:

```text
src/grocery_assistant_mcp/stdio_server.py
```

Command:

```bash
python -m grocery_assistant_mcp.stdio_server
```

The stdio server is useful for local MCP clients and MCP Inspector testing.

---

### Streamable HTTP Server

File path:

```text
src/grocery_assistant_mcp/streamable_http_server.py
```

Command:

```bash
python -m grocery_assistant_mcp.streamable_http_server
```

The Streamable HTTP server is useful for testing MCP over HTTP.

A browser request to `/` may return `404 Not Found`. This does not necessarily mean the MCP server is broken. The server is intended for MCP client connections, not as a normal website.

---

## Testing with Curl over Streamable HTTP

Curl can be used as a simple manual MCP client for testing the Streamable HTTP server without relying on MCP Inspector or a full MCP host. This is useful for confirming the raw MCP request and response flow.

Curl testing is especially useful for checking:

* Whether the `/mcp` endpoint accepts valid MCP JSON-RPC requests
* Whether the server initializes correctly
* Whether the server returns and accepts an `mcp-session-id`
* Whether resources, tools, and prompts are listed correctly
* Whether individual resources can be read through their MCP URIs
* Whether future write tools can be tested safely and repeatably

### Important Curl Testing Concepts

MCP Streamable HTTP requests use JSON-RPC messages sent to the `/mcp` endpoint.

A normal browser request such as:

```text
GET /mcp
```

may return `406 Not Acceptable`. This does not necessarily mean the server is broken. The MCP endpoint expects a valid MCP JSON-RPC request with appropriate HTTP headers.

The normal curl testing lifecycle is:

```text
1. Send initialize request
2. Copy the returned mcp-session-id response header
3. Send notifications/initialized using that session ID
4. Send resources/list, resources/read, tools/list, tools/call, prompts/list, or prompts/get using the same session ID
```

The difference between the JSON-RPC request ID and the MCP session ID is important:

```text
JSON-RPC id:
- included inside the JSON body
- changes for each request
- matches a response to a specific request

mcp-session-id:
- included as an HTTP header
- usually stays the same for the initialized MCP session
- tells the server which initialized client session the request belongs to
```

### Suggested Curl Test Folder

A useful project structure for curl testing is:

```text
grocery-assistant-mcp/
│
├── curl_requests/
│   ├── 01_initialize.json
│   ├── 02_initialized_notification.json
│   ├── 03_resources_list.json
│   ├── 04_read_inventory.json
│   ├── 05_read_intake_history.json
│   ├── 06_read_intake_items.json
│   ├── 07_tools_list.json
│   └── 08_prompts_list.json
│
├── src/
│   └── grocery_assistant_mcp/
│
├── README.md
└── pyproject.toml
```

Run curl commands from the folder that contains the `curl_requests` directory. If the terminal is in a different folder, either change directory first or use a full file path.

Example:

```powershell
cd C:\Users\shann\TafeLocal\rest-at2\grocery-assistant-mcp
```

### 1. Initialize the MCP Session

Create:

```text
curl_requests/01_initialize.json
```

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

Run:

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" --data-binary "@curl_requests/01_initialize.json"
```

A successful response should return `HTTP/1.1 200 OK` and an `mcp-session-id` header.

Example response header:

```text
mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e
```

Copy this value and reuse it in later requests.

The response body may use Server-Sent Events formatting:

```text
event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}
```

The useful JSON-RPC response is inside the `data:` line.

### 2. Send the Initialized Notification

Create:

```text
curl_requests/02_initialized_notification.json
```

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

Run, replacing the session ID with the value returned by the initialize response:

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e" --data-binary "@curl_requests/02_initialized_notification.json"
```

This completes the MCP setup lifecycle for the curl client.

### 3. List MCP Resources

Create:

```text
curl_requests/03_resources_list.json
```

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/list"
}
```

Run:

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e" --data-binary "@curl_requests/03_resources_list.json"
```

Expected Version 1 resources include:

```text
grocery://inventory
grocery://intake-history
grocery://intake-items
```

This confirms that the MCP resource registration is working.

### 4. Read the Inventory Resource

Create:

```text
curl_requests/04_read_inventory.json
```

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
curl.exe -i -X POST "http://127.0.0.1:8000/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e" --data-binary "@curl_requests/04_read_inventory.json"
```

This confirms the full read path:

```text
curl request
→ Streamable HTTP MCP endpoint
→ MCP resources/read method
→ grocery://inventory resource
→ CSV-backed inventory data
→ JSON-RPC response
```

### 5. Read Intake Resources

Create:

```text
curl_requests/05_read_intake_history.json
```

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/read",
  "params": {
    "uri": "grocery://intake-history"
  }
}
```

Create:

```text
curl_requests/06_read_intake_items.json
```

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {
    "uri": "grocery://intake-items"
  }
}
```

Run each file with the same curl pattern:

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e" --data-binary "@curl_requests/05_read_intake_history.json"
```

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e" --data-binary "@curl_requests/06_read_intake_items.json"
```

### 6. List MCP Tools

Create:

```text
curl_requests/07_tools_list.json
```

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/list"
}
```

Run:

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e" --data-binary "@curl_requests/07_tools_list.json"
```

Expected Version 1 tools include:

```text
search_inventory
get_recent_intake
get_daily_intake_summary
```

This confirms that the MCP tool registration is working.

### 7. List MCP Prompts

Create:

```text
curl_requests/08_prompts_list.json
```

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "prompts/list"
}
```

Run:

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e" --data-binary "@curl_requests/08_prompts_list.json"
```

Expected Version 1 prompts include:

```text
summarise_inventory
find_inventory_items
suggest_meals_from_inventory
review_recent_intake
review_daily_intake
suggest_next_meal
```

### Reading Curl Output More Cleanly

Streamable HTTP responses may be returned as `text/event-stream`. In that case, the MCP response is wrapped like this:

```text
event: message
data: {"jsonrpc":"2.0","id":3,"result":{...}}
```

For resource reads, the resource content is usually inside:

```text
result.contents[0].text
```

If the resource content is JSON text, it may appear escaped in the raw terminal output. This is expected.

A PowerShell-only way to display the inventory resource as a cleaner table is:

```powershell
$response = curl.exe -s -X POST "http://127.0.0.1:8000/mcp" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -H "mcp-session-id: 31f8ff0588604c3f9021baae3df88c0e" `
  --data-binary "@curl_requests/04_read_inventory.json"

$jsonLine = ($response | Select-String "^data: ").ToString().Replace("data: ", "")
$mcpJson = $jsonLine | ConvertFrom-Json
$inventoryText = $mcpJson.result.contents[0].text
$inventory = $inventoryText | ConvertFrom-Json
$inventory | Format-Table stock_id, food_item, quantity, unit, servings_remaining, stock_status, expiry_date
```

The cleaned output is easier to inspect than the raw escaped JSON string.

### Common Curl Testing Issues

#### File Not Found

If curl returns:

```text
curl: Failed to open curl_requests/01_initialize.json
```

then the terminal is not currently in the folder that contains `curl_requests`, or the file has not been created.

Check the current folder:

```powershell
pwd
```

Check whether the request file exists:

```powershell
dir curl_requests
```

#### Invalid JSON Parse Error

If the server returns a JSON parse error, use request files with `--data-binary` instead of typing large JSON bodies directly into PowerShell.

Recommended pattern:

```powershell
--data-binary "@curl_requests/01_initialize.json"
```

This avoids quoting problems where PowerShell changes how JSON is passed to curl.

#### Browser 404 or 406 Responses

A browser request to `/` may return `404 Not Found`.

A browser request to `/mcp` may return `406 Not Acceptable`.

These responses do not necessarily mean the MCP server is broken. The `/mcp` endpoint expects proper MCP JSON-RPC requests, not normal browser page requests.

### Curl Testing Checklist

A useful Version 1 curl test sequence is:

```text
1. Start the Streamable HTTP server.
2. Send 01_initialize.json.
3. Copy the returned mcp-session-id.
4. Send 02_initialized_notification.json with the session ID.
5. Send 03_resources_list.json.
6. Confirm grocery://inventory, grocery://intake-history, and grocery://intake-items are listed.
7. Send 04_read_inventory.json.
8. Confirm inventory CSV data is returned.
9. Send 05_read_intake_history.json.
10. Send 06_read_intake_items.json.
11. Send 07_tools_list.json.
12. Confirm read-only tools are listed.
13. Send 08_prompts_list.json.
14. Confirm inventory and intake prompts are listed.
```

This gives a repeatable manual test path for the Version 1 MCP server.

---

## Testing with MCP Inspector

MCP Inspector can be used as a local testing client for Version 1.

Suggested test order:

1. Start the server from the project root.
2. Connect with MCP Inspector.
3. Confirm the resources are listed.
4. Read `grocery://inventory`.
5. Read `grocery://intake-history`.
6. Read `grocery://intake-items`.
7. Confirm `search_inventory` appears in the tools list.
8. Test `search_inventory` with a query, category, or location.
9. Confirm `get_recent_intake` appears in the tools list.
10. Test `get_recent_intake` with the default 7-day window.
11. Confirm `get_daily_intake_summary` appears in the tools list.
12. Test `get_daily_intake_summary` with a known date from the CSV file.
13. Confirm all inventory prompts are listed.
14. Confirm all intake prompts are listed.
15. Test prompt-guided workflows through the client.

---

## Suggested Version 1 Build Order

The current implementation can be understood and tested in this order.

### Phase 1 - Core Service

Main file:

```text
src/grocery_assistant_mcp/core/grocery_service.py
```

Purpose:

* Read CSV data.
* Convert DataFrames to records.
* Convert records to JSON.
* Search inventory.
* Get recent intake.
* Build daily intake summaries.

Expected result:

* Service functions work independently before being exposed through MCP.

---

### Phase 2 - Resources

Main files:

```text
src/grocery_assistant_mcp/mcp_resources/inventory_resources.py
src/grocery_assistant_mcp/mcp_resources/intake_resources.py
```

Purpose:

* Expose inventory as `grocery://inventory`.
* Expose meal-level intake as `grocery://intake-history`.
* Expose item-level intake as `grocery://intake-items`.

Expected result:

* MCP Inspector can list and read all Version 1 resources.

---

### Phase 3 - Tools

Main files:

```text
src/grocery_assistant_mcp/mcp_tools/inventory_tools.py
src/grocery_assistant_mcp/mcp_tools/intake_tools.py
```

Purpose:

* Expose inventory search.
* Expose recent intake retrieval.
* Expose daily intake summary retrieval.

Expected result:

* MCP Inspector can list and call all Version 1 tools.
* Tool results match the underlying CSV data.

---

### Phase 4 - Prompts

Main files:

```text
src/grocery_assistant_mcp/mcp_prompts/inventory_prompts.py
src/grocery_assistant_mcp/mcp_prompts/intake_prompts.py
```

Purpose:

* Guide inventory summaries.
* Guide inventory item searches.
* Guide meal suggestions from inventory.
* Guide recent intake reviews.
* Guide daily intake reviews.
* Guide next-meal suggestions.

Expected result:

* MCP Inspector can list all Version 1 prompts.
* Prompts guide the assistant to use the correct resources and tools.
* Prompts preserve the read-only boundaries of Version 1.

---

### Phase 5 - Combined Workflow Testing

Purpose:

* Test resources, tools, and prompts together.
* Confirm the assistant reads data before answering.
* Confirm prompt-guided workflows call the appropriate resources or tools.
* Confirm no Version 1 workflow implies that records are modified.

Example workflow:

1. Read `grocery://inventory`.
2. Use `summarise_inventory` to organise the available food.
3. Use `suggest_meals_from_inventory` to suggest meals.
4. Use `get_daily_intake_summary` to review today's intake.
5. Use `suggest_next_meal` to recommend a suitable next meal.

Expected result:

* The Version 1 server supports practical read-only grocery assistant workflows.

---

## Example Assistant Workflows

### Summarise Current Inventory

Possible flow:

1. User asks: "What food do I currently have?"
2. Client reads `grocery://inventory`.
3. Assistant groups the inventory into practical categories.
4. Assistant identifies low-stock, empty, or soon-to-use items if the data is available.
5. Assistant suggests possible meal opportunities.

---

### Find a Specific Inventory Item

Possible flow:

1. User asks: "Do I have chicken in the freezer?"
2. Client uses `search_inventory` with a query and location filter.
3. Assistant summarises matching items, quantity, location, stock status, and expiry date if available.
4. If no result is found, the assistant clearly says no matching item was found.

---

### Review Recent Intake

Possible flow:

1. User asks: "What have I been eating recently?"
2. Client uses `get_recent_intake`.
3. Assistant summarises recent meals, repeated patterns, likely protein and carbohydrate sources, and variety.
4. Assistant gives practical next-meal suggestions without medical advice or strict dieting language.

---

### Review a Specific Day

Possible flow:

1. User asks: "How did I eat on 2026-05-11?"
2. Client uses `get_daily_intake_summary(date="2026-05-11")`.
3. Assistant reviews meals, item details, estimated nutrition totals, and missing nutrition data.
4. Assistant suggests what type of meal may fit next.

---

### Suggest the Next Meal

Possible flow:

1. User asks: "What should I eat next?"
2. Client uses `get_daily_intake_summary` for the selected date.
3. Client reads `grocery://inventory`.
4. Client may use `search_inventory` if a specific ingredient, category, or location needs checking.
5. Assistant recommends a meal, explains why it fits, lists inventory ingredients, notes missing ingredients, and gives simple cooking steps.

---

## Version 1 Boundary

Version 1 currently focuses on read-only assistant workflows.

Current resources, tools, and prompts can help the assistant inspect, search, summarise, review, and suggest. They do not currently provide write tools for adding meals, updating inventory, reducing servings, deleting records, or saving meal plans.

This boundary is useful for early MCP testing because it allows the project to confirm that the server, resources, tools, prompts, and client behaviour are working correctly before adding write operations.
