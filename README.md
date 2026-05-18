# Grocery Assistant MCP

A local Model Context Protocol (MCP) server for managing grocery inventory, meal intake records, inventory consumption, and food waste tracking.

This project is built as a learning-focused MCP implementation. It exposes grocery data through MCP resources and provides tools that allow an MCP client or agent to search, add, update, remove, and connect grocery inventory with food intake workflows.

---

## Current Version

```text
Version 1.4
```

Version 1.4 focuses on improving the project from simple read/write tools into a more complete grocery workflow system.

The current Version 1.4 implementation includes:

- Inventory search and write tools
- Intake history and intake item tools
- Update and remove workflows for inventory and intake
- Inventory consumption tracking
- Food waste tracking through removal workflows
- Batch meal logging
- Batch meal logging with inventory deduction
- MCP resources for inspecting CSV-backed data
- Curl-based MCP workflow testing
- MCP Inspector testing support
- Reorganized documentation for Version 1.4 closeout

---

## Project Goals

The project is designed to explore how an MCP server can support a grocery assistant that can:

- Track what food is currently available
- Keep useful out-of-stock or low-stock items for future grocery reasoning
- Log meals and intake history
- Link meals to inventory where appropriate
- Deduct inventory when tracked food is consumed
- Record food waste when items are removed for waste-related reasons
- Provide structured resources and tools that an MCP-compatible client can use
- Support future agent workflows such as meal planning, grocery list suggestions, and habit-aware recommendations

---

## Current Documentation Layout

Documentation is currently organized under:

```text
docs/
  docs/
    index.md

    guides/
      command_reference_v1_4.md
      mcp_testing_guide_v1_4.md

    checklists/
      version_1_4_closeout_checklist.md

    journals/
      development_journal.md

    roadmap/
      project_roadmap.md

    planning/
      future_version_plans.md

    concepts/
      mcp_grocery_learning_concept.md

    archive/
      originals/
        old and superseded documentation files

  version_1_4_curl/
    curl_requests/
    curl_responses/
```

The most important active documents are:

```text
docs/docs/guides/command_reference_v1_4.md
docs/docs/guides/mcp_testing_guide_v1_4.md
docs/docs/checklists/version_1_4_closeout_checklist.md
docs/docs/roadmap/project_roadmap.md
docs/docs/planning/future_version_plans.md
```

The archived files are kept for history only. They should not be treated as the current source of truth.

---

## Main MCP Capabilities

### Inventory Tools

The inventory workflow supports:

- Searching inventory
- Adding new inventory items
- Updating existing inventory items
- Removing inventory items from active inventory
- Recording waste when the removal reason is waste-related
- Consuming inventory without creating an intake item
- Consuming inventory as part of a logged meal

Expected inventory concepts include:

- `stock_id`
- `food_item`
- `brand`
- `category`
- `location`
- `quantity`
- `unit`
- `servings_remaining`
- `stock_status`
- `expiry_date`
- `notes`

Version 1.4 stock status values include:

```text
in_stock
low
very_low
out
expired
```

---

### Intake Tools

The intake workflow supports:

- Adding a parent meal or eating event
- Adding child intake items to a meal
- Updating intake entries
- Updating intake items
- Removing intake items
- Removing parent intake entries when safe
- Searching intake records
- Getting recent intake
- Getting a daily intake summary

The intake system separates:

```text
Parent meal entries
Child food/item/component rows
```

This allows a meal such as spaghetti bolognese to have one parent entry and multiple child items such as spaghetti, beef mince, tomato sauce, vegetables, or cheese.

---

### Batch Meal Tools

Version 1.4 adds batch meal workflows.

#### `add_meal_with_items`

Use this for intake-only meal logging.

This tool creates:

```text
user_intake_history.csv
user_intake_items.csv
```

It does not deduct inventory.

Use this when the meal should be logged, but the inventory should not be changed.

#### `add_meal_with_inventory_items`

Use this for inventory-linked meal logging.

This tool creates or updates:

```text
user_intake_history.csv
user_intake_items.csv
user_inventory.csv
user_inventory_consumption.csv
```

It creates the meal, creates child intake items, deducts selected inventory items, and records linked inventory consumption events.

Use this when the meal clearly used tracked inventory items.

---

### Resources

The MCP server exposes CSV-backed data as MCP resources.

Common resources include:

```text
grocery://inventory
grocery://intake/history
grocery://intake/items
grocery://inventory/consumption
grocery://food-waste
```

Use MCP resource listing to confirm the exact resource URIs registered by the current implementation.

---

## Data Storage

The project uses local CSV files as its current persistence layer.

This is intentional for Version 1 development because CSVs make it easy to:

- Inspect changes manually
- Write focused tests
- Understand the data model
- Debug MCP requests and responses
- Avoid introducing database complexity too early

Future versions may migrate to a database or add a repository abstraction, but CSV-backed storage is appropriate for the current learning and prototype stage.

---

## Running the Test Suite

From the project root:

```powershell
pytest -q
```

Run focused Version 1.4 tests:

```powershell
pytest tests/test_batch_meal_service.py -q
pytest tests/test_batch_inventory_meal_service.py -q
pytest tests/test_mcp_tool_registration.py -q
pytest tests/test_mcp_resource_registration.py -q
```

---

## Starting the MCP Server

From the project root:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected endpoint:

```text
http://127.0.0.1:8000/mcp
```

The root URL may return:

```text
404 Not Found
```

That is expected because the MCP endpoint is `/mcp`.

---

## MCP Inspector

Start the server first.

Then in a second terminal:

```powershell
npx @modelcontextprotocol/inspector
```

Use:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
```

The MCP Inspector is useful for manually checking:

- Registered tools
- Registered resources
- Tool schemas
- Resource reads
- Tool calls
- Validation errors

---

## Curl Testing

Version 1.4 curl requests are currently stored in:

```text
docs/version_1_4_curl/curl_requests/
```

Curl responses are stored in:

```text
docs/version_1_4_curl/curl_responses/
```

The active curl guide is:

```text
docs/docs/guides/command_reference_v1_4.md
```

The active testing guide is:

```text
docs/docs/guides/mcp_testing_guide_v1_4.md
```

The current curl workflow is designed to run from a clean dataset where CSV files contain only header rows.

The workflow creates its own test records through MCP tools, rather than depending on stale manually seeded data.

---

## Current Curl Request Groups

```text
docs/version_1_4_curl/curl_requests/
  00_initialize.json
  01_initialized_notification.json
  02_list_tools.json
  03_list_resources.json

  inventory/
    10_add_inventory_spaghetti.json
    11_add_inventory_beef_mince.json
    12_add_inventory_tomato_sauce.json
    13_search_inventory_all.json
    14_search_inventory_protein.json
    15_update_inventory_beef_mince_low.json
    16_search_inventory_low_stock.json

  batch_meals/
    20_add_meal_with_items_intake_only.json
    21_add_meal_with_inventory_items_spag_bog.json

  intake/
    30_search_intake_by_date.json
    31_search_intake_spaghetti.json

  resources/
    40_read_inventory_resource.json
    41_read_intake_history_resource.json
    42_read_intake_items_resource.json
    43_read_inventory_consumption_resource.json
    44_read_food_waste_resource.json

  validation/
    50_add_inventory_missing_food_item.json
    51_add_inventory_negative_quantity.json
    52_update_inventory_unknown_id.json
    53_add_intake_invalid_date.json
```

---

## Recommended Manual Curl Flow

From the `docs` folder:

```powershell
$RequestRoot = "version_1_4_curl/curl_requests"
$ResponseRoot = "version_1_4_curl/curl_responses"
New-Item -ItemType Directory -Force $ResponseRoot | Out-Null
```

Initialize the MCP session:

```powershell
curl.exe -i -s -X POST "http://127.0.0.1:8000/mcp" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  --data-binary "@$RequestRoot/00_initialize.json" `
  -D "$ResponseRoot/00_initialize_headers.txt" `
  -o "$ResponseRoot/00_initialize_raw.txt"

$SessionId = (Select-String -Path "$ResponseRoot/00_initialize_headers.txt" -Pattern "^mcp-session-id:\s*(.+)$").Matches[0].Groups[1].Value.Trim()
$SessionId
```

Send initialized notification:

```powershell
curl.exe -s -X POST "http://127.0.0.1:8000/mcp" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -H "mcp-session-id: $SessionId" `
  --data-binary "@$RequestRoot/01_initialized_notification.json" `
  -o "$ResponseRoot/01_initialized_notification_raw.txt"
```

The command reference includes a helper function that saves each MCP response as both:

```text
*.raw.txt
*.json
```

Use the `.json` files for readable inspection.

---

## Clean Dataset Testing

Version 1.4 closeout testing should be performed from a clean local dataset.

For this project, “clean” means the CSV files exist but contain only header rows.

This helps confirm that:

- Tools can create records from scratch
- ID generation works correctly
- No request depends on stale test data
- Inventory deductions are observable
- Intake records are observable
- Resource reads reflect the current CSV state
- Validation errors do not corrupt data

---

## Important Design Notes

### Why Keep Some Out-of-Stock Items?

The project intentionally allows some out-of-stock items to remain represented in inventory.

This is useful because out-of-stock items may still help future grocery reasoning. For example, they can show:

- Common staples
- Frequently purchased items
- Low-priority items that do not need urgent replacement
- Ingredients that are normally kept on hand
- Items that were previously used in meals

Removal is still supported when an item should leave active tracking.

---

### Why Separate Intake Entries and Intake Items?

Parent intake entries represent the eating event.

Child intake items represent the components of the meal.

This separation supports:

- Better meal summaries
- Item-level nutrition estimates
- Inventory-linked food usage
- Future meal templates
- Future meal recommendation logic
- Safer update and remove workflows

---

### Why Separate Inventory Consumption?

Inventory consumption records provide a history of how tracked inventory was used.

This allows the assistant to reason about:

- Usage patterns
- Frequently consumed items
- Ingredients used in meals
- Stock depletion over time
- Future grocery planning

---

## Version Status

Version 1.4 is intended to be closed after:

- Full pytest suite passes
- MCP Inspector smoke testing passes
- Curl workflow passes from a clean dataset
- Resource reads confirm final data state
- Validation requests fail safely
- Documentation is committed in its reorganized structure

See:

```text
docs/docs/checklists/version_1_4_closeout_checklist.md
```

---

## Suggested Git Workflow

After confirming tests and curl workflow:

```powershell
git status
git add README.md docs/
git commit -m "docs: finalize version 1.4 documentation"
```

Then push:

```powershell
git push
```

---

## Future Direction

Likely future versions may explore:

- Grocery list generation
- Meal suggestion prompts
- Meal templates
- Pantry-aware planning
- Smarter stock status updates
- Better nutrition summaries
- Stronger food waste analytics
- Database-backed persistence
- Agent-driven workflows through MCP clients

See:

```text
docs/docs/planning/future_version_plans.md
docs/docs/roadmap/project_roadmap.md
```

---

## Notes for Contributors

This project is intentionally incremental.

When adding a new capability:

1. Add or update the service-layer function.
2. Add tests for the service-layer behavior.
3. Register the MCP tool or resource.
4. Add MCP registration tests.
5. Add or update curl request examples.
6. Update the command/testing documentation.
7. Run the full test suite.
8. Commit the versioned change.

The goal is to keep MCP behavior understandable, testable, and traceable back to the CSV-backed service layer.
