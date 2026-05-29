# Grocery Assistant MCP

A local Model Context Protocol (MCP) server for managing grocery inventory, meal intake records, inventory consumption, planning signals, recommendation drafts, and provider-agent client workflows.

This project is built as a learning-focused MCP implementation. The MCP server exposes grocery data through resources and tools, while the client layer connects model providers such as OpenAI, Gemini, or a local OpenAI-compatible model to those MCP tools.

The main design principle is:

```text
MCP server = deterministic grocery tools and business logic
Provider clients = model/agent connections to the MCP server
Agents/models = reasoning, tool selection, and explanation
```

---

## Current Version

```text
Version 1.6 — Client and Agent Integration
```

Version 1.6 adds a major new capability: provider-agent clients that can connect model providers to the Grocery Assistant MCP server.

The current implementation includes:

- Inventory search and write tools
- Intake history and intake item tools
- Update and remove workflows for inventory and intake
- Inventory consumption tracking
- Food waste tracking through removal workflows
- Batch meal logging
- Batch meal logging with inventory deduction
- Planning context review tools
- Low-stock and use-soon review tools
- Inventory data-quality review tools
- Draft restock suggestion tools
- Draft meal suggestion tools
- MCP resources for inspecting CSV-backed data
- Curl-based MCP workflow testing
- MCP Inspector testing support
- Deterministic Python MCP smoke client
- Provider-agent clients for OpenAI, Gemini, and local OpenAI-compatible models
- Shared client safety policy for read/write tool exposure
- Unit tests for client policy, schemas, config, and MCP result formatting

---

## Project Goals

The project is designed to explore how an MCP server can support a grocery assistant that can:

- Track what food is currently available
- Keep useful out-of-stock or low-stock items for future grocery reasoning
- Log meals and intake history
- Link meals to inventory where appropriate
- Deduct inventory when tracked food is consumed
- Record food waste when items are removed for waste-related reasons
- Review planning context from existing grocery records
- Draft meal and restock suggestions from structured signals
- Provide structured resources and tools that an MCP-compatible client can use
- Support provider-agent workflows through OpenAI, Gemini, and local model clients
- Preserve deterministic service-layer behaviour while allowing agents to reason over tool results

---

## Mental Model

The project has three layers:

```text
CSV-backed data and service layer
  ↓
MCP server tools and resources
  ↓
Provider clients and agents
```

The MCP server remains the source of truth. Agents do not directly edit CSV files and do not replace service-layer validation. Agents can only work through exposed MCP tools.

The client layer is responsible for:

- connecting to the MCP server
- connecting to a model provider
- exposing allowed tools to the provider
- applying read/write tool safety policy
- logging visible tool calls
- returning the final model response to the terminal

---

## Documentation Layout

Documentation is organized under:

```text
docs/
  docs/
    index.md

    guides/
      command_reference_v1_4.md
      mcp_testing_guide_v1_4.md
      client_agent_integration.md

    checklists/
      version_1_4_closeout_checklist.md
      version_1_6_client_agent_closeout_checklist.md

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
      client_agent/

  version_1_4_curl/
    curl_requests/
    curl_responses/
```

The most important active documents for Version 1.6 are:

```text
docs/docs/guides/client_agent_integration.md
docs/docs/checklists/version_1_6_client_agent_closeout_checklist.md
docs/docs/journals/development_journal.md
```

The older Version 1.4 curl and MCP Inspector documentation remains useful for lower-level MCP testing.

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

Common stock status values include:

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

Batch meal workflows support two different use cases.

#### `add_meal_with_items`

Use this for intake-only meal logging.

This tool creates records in:

```text
user_intake_history.csv
user_intake_items.csv
```

It does not deduct inventory.

Use this when the meal should be logged, but the inventory should not be changed.

#### `add_meal_with_inventory_items`

Use this for inventory-linked meal logging.

This tool creates or updates records in:

```text
user_intake_history.csv
user_intake_items.csv
user_inventory.csv
user_inventory_consumption.csv
```

It creates the meal, creates child intake items, deducts selected inventory items, and records linked inventory consumption events.

Use this when the meal clearly used tracked inventory items.

---

### Planning and Recommendation Draft Tools

The planning layer derives temporary signals from existing grocery records.

Current planning and recommendation tools include:

```text
review_planning_context
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
draft_restock_suggestions_tool
draft_meal_suggestions_tool
```

These tools are intended to support agent reasoning without making automatic changes to stored data.

Important rule:

```text
Review and draft tools should not mutate stored records.
```

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

## Client and Agent Integration

Version 1.6 adds provider-agent clients under:

```text
clients/
  mcp_smoke_client.py

  shared/
    config.py
    instructions.py
    mcp_helpers.py
    openai_agents_filter.py
    schema_adapters.py
    tool_logging.py
    tool_policy.py

  providers/
    openai_agent_client.py
    gemini_agent_client.py
    local_agent_client.py
```

### Client Roles

| Client | Role | Cost profile | Recommended use |
|---|---|---:|---|
| `clients.mcp_smoke_client` | Direct MCP connection test with no LLM | Free | First test after starting server |
| `clients.providers.openai_agent_client` | Primary MCP-capable provider agent | Paid API | Best quality end-to-end agent test |
| `clients.providers.gemini_agent_client` | MCP-capable Gemini comparison agent | Free/low-cost tier | Provider comparison and lower-cost checks |
| `clients.providers.local_agent_client` | MCP-capable local OpenAI-compatible experiment | Local compute | Offline/cheap experimentation |

### Safety Policy

By default, provider clients expose read/review/draft tools only.

Write tools require either:

```powershell
--allow-writes
```

or:

```env
GROCERY_AGENT_ALLOW_WRITES=true
```

This prevents normal advice and review prompts from accidentally mutating local CSV data.

---

## Environment Configuration

Create a private `.env` file locally:

```env
OPENAI_API_KEY=your_real_openai_key_here
GEMINI_API_KEY=your_real_gemini_key_here
GROCERY_MCP_URL=http://127.0.0.1:8000/mcp

OPENAI_AGENT_MODEL=gpt-5.4-mini
GEMINI_MODEL=gemini-2.5-flash
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5:1.5b

GROCERY_AGENT_ALLOW_WRITES=false
GROCERY_AGENT_MAX_TOOL_ROUNDS=4
GROCERY_AGENT_MAX_RESULT_CHARS=8000
```

Never commit `.env`.

The committed `.env.example` should contain placeholders only.

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

## Running the Test Suite

From the project root:

```powershell
pytest -q
```

Run focused client tests:

```powershell
pytest tests/clients -q
```

Run syntax checks:

```powershell
python -m compileall clients
```

---

## Running the MCP Smoke Client

Start the MCP server first.

Then run:

```powershell
python -m clients.mcp_smoke_client
```

Optional:

```powershell
python -m clients.mcp_smoke_client --show-resources --show-prompts
```

The smoke client should:

- connect to the MCP server
- list available tools
- call `search_inventory`
- print a compact inventory summary

Use this before running paid or provider-specific agents.

---

## Running Provider Agent Clients

Run provider clients from the project root.

### OpenAI provider

```powershell
python -m clients.providers.openai_agent_client "Review my current grocery planning context and suggest useful next actions."
```

OpenAI is the primary high-confidence agent path. Because it uses a paid API, use smoke tests and cheaper provider tests first.

### Gemini provider

```powershell
python -m clients.providers.gemini_agent_client "Review my current grocery planning context and suggest useful next actions."
```

Gemini is useful for lower-cost provider comparison and free-tier testing.

### Local provider

```powershell
python -m clients.providers.local_agent_client "Review my current grocery planning context and suggest useful next actions."
```

The local provider is experimental. It depends on the selected local model and local runtime support for OpenAI-compatible chat/tool behaviour.

---

## Explicit Write-Mode Testing

Use write mode only for deliberate, reversible development tests.

Example:

```powershell
python -m clients.providers.openai_agent_client --allow-writes "Add a test inventory item called Test Apples with quantity 1 each."
```

Recommended process:

```text
1. Add a clearly named test item.
2. Search for the test item.
3. Remove the test item by exact stock_id.
4. Confirm it is gone.
```

Do not use write mode for normal planning, review, meal suggestion, or restock suggestion prompts.

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

The older Version 1.4 curl workflow remains useful for low-level MCP request testing.

Curl requests are stored in:

```text
docs/version_1_4_curl/curl_requests/
```

Curl responses are stored in:

```text
docs/version_1_4_curl/curl_responses/
```

The curl workflow creates its own test records through MCP tools, rather than depending on stale manually seeded data.

For full details, see:

```text
docs/docs/guides/command_reference_v1_4.md
docs/docs/guides/mcp_testing_guide_v1_4.md
```

---

## Important Design Notes

### Why Keep Deterministic MCP Tools?

The agent should not become the source of truth.

The service layer and MCP tools remain responsible for:

- validation
- record creation
- record updates
- relationship safety
- inventory deduction
- resource exposure
- structured response contracts

Agents can reason over tool results, but they should not bypass the deterministic MCP layer.

### Why Separate Provider Clients?

The project now supports multiple provider-agent clients:

```text
OpenAI
Gemini
Local OpenAI-compatible model
```

Each provider can have different internal mechanics, but the project keeps the same outer client shape:

```text
terminal request
  -> provider client
  -> model/provider
  -> allowed MCP tools
  -> final response
```

This makes provider comparison easier and keeps the difference focused on model quality, cost, speed, and reliability.

### Why Gate Write Tools?

Write tools can mutate local CSV data. By default, the provider clients expose only read/review/draft tools.

This supports safe development:

```text
Normal mode = inspect, review, draft, explain
Write mode = explicit data mutation only when enabled
```

---

## Future Direction

Likely future versions may explore:

- stronger provider comparison tests
- token/cost tracking for paid provider calls
- provider response quality evaluation
- explicit approval prompts for write tools
- MCP prompt templates for common grocery workflows
- grocery list generation
- richer meal planning workflows
- nutrition-aware recommendation refinement
- database-backed persistence
- long-term feedback and preference learning

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
5. Update deterministic clients or provider clients when the tool surface changes.
6. Add or update curl, smoke, or provider test examples.
7. Update the command/testing documentation.
8. Run the full test suite.
9. Commit the versioned change.

The goal is to keep MCP behavior understandable, testable, and traceable back to the CSV-backed service layer.
