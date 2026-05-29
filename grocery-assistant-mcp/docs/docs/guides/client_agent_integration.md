# Client and Agent Integration

## Purpose

This document explains the Version 1.6 client-agent implementation for the Grocery Assistant MCP project.

Version 1.6 introduces a provider-client layer that lets different model providers connect to the same Grocery Assistant MCP server.

The implementation is designed around one core idea:

```text
Same Grocery MCP server.
Same shared safety policy.
Same terminal-facing provider structure.
Different model/provider quality.
```

This document should be treated as the main onboarding guide for the client-agent layer.

---

## Mental Model

The project now has three major layers:

```text
CSV-backed service layer
  = deterministic records, validation, update logic, and business rules

MCP server
  = exposes service-layer functionality as MCP tools and resources

Provider clients
  = connect OpenAI, Gemini, or a local model to the MCP server
```

The agent does not replace the server.

The server remains responsible for:

- validating inputs
- maintaining CSV records
- exposing tools
- exposing resources
- preserving relationship safety
- returning structured results

The client layer is responsible for:

- connecting to the MCP server
- connecting to a model provider
- exposing only allowed tools
- applying read/write safety policy
- logging tool calls clearly
- returning final model output to the terminal

The model/provider is responsible for:

- interpreting the user request
- deciding whether tools are useful
- choosing allowed tools
- explaining the result in natural language

---

## Final Folder Layout

```text
clients/
  __init__.py
  mcp_smoke_client.py

  shared/
    __init__.py
    cli.py
    config.py
    instructions.py
    mcp_helpers.py
    openai_agents_filter.py
    schema_adapters.py
    tool_logging.py
    tool_policy.py

  providers/
    __init__.py
    openai_agent_client.py
    gemini_agent_client.py
    local_agent_client.py

tests/
  clients/
    test_config_and_instructions.py
    test_mcp_helpers.py
    test_schema_adapters.py
    test_tool_policy.py
```

---

## Client Roles

| Client | MCP connected | Model connected | Role |
|---|---:|---:|---|
| `clients.mcp_smoke_client` | Yes | No | Deterministic MCP connectivity test |
| `clients.providers.openai_agent_client` | Yes | Yes | Primary high-confidence MCP agent |
| `clients.providers.gemini_agent_client` | Yes | Yes | Free-tier / lower-cost MCP-capable comparison agent |
| `clients.providers.local_agent_client` | Yes | Yes | Experimental local MCP-capable agent |

---

## Why Keep `mcp_smoke_client.py` Separate?

The smoke client is not a provider client.

It answers a simpler question:

```text
Can Python connect to the MCP server and call a grocery tool?
```

It should be run before provider-agent clients because it isolates MCP server problems from model/provider problems.

Run it with:

```powershell
python -m clients.mcp_smoke_client
```

Optional:

```powershell
python -m clients.mcp_smoke_client --show-resources --show-prompts
```

Expected behaviour:

- pings the MCP server
- lists tools
- calls `search_inventory`
- prints a compact inventory summary

---

## Provider Client Design

Each provider client should be runnable from the project root with `python -m`.

Examples:

```powershell
python -m clients.providers.openai_agent_client "What items should I use soon?"
python -m clients.providers.gemini_agent_client "What items should I use soon?"
python -m clients.providers.local_agent_client "What items should I use soon?"
```

Each provider client should follow the same outer structure:

```text
load configuration
parse terminal request
build or connect provider model
connect to MCP server
expose allowed tools
run the request
print final output
```

The internals can differ by provider.

---

## OpenAI Provider

File:

```text
clients/providers/openai_agent_client.py
```

Role:

```text
Primary paid, high-confidence MCP agent path.
```

The OpenAI provider uses the OpenAI Agents SDK MCP integration. It is the cleanest full agent path because the SDK can connect the agent to the MCP server and handle tool discovery/tool calls.

Use this provider for the most realistic end-to-end agent test:

```powershell
python -m clients.providers.openai_agent_client "Review my current grocery planning context and suggest useful next actions."
```

Because this path uses a paid API, run deterministic and cheaper checks first:

```powershell
python -m clients.mcp_smoke_client
python -m clients.providers.gemini_agent_client "Review my planning context."
python -m clients.providers.local_agent_client "Review my planning context."
```

---

## Gemini Provider

File:

```text
clients/providers/gemini_agent_client.py
```

Role:

```text
Lower-cost MCP-capable comparison provider.
```

The earlier Gemini experiment proved the idea of Gemini function calling against MCP tools, but the old all-in-one file mixed too many concerns:

```text
environment loading
manual schemas
tool allowlists
Gemini function declarations
function-call extraction
MCP execution
result compaction
final response generation
```

The new design keeps the provider file smaller by moving shared concerns into `clients/shared/`.

Use Gemini when you want a lower-cost provider comparison:

```powershell
python -m clients.providers.gemini_agent_client "Review my current grocery planning context and suggest useful next actions."
```

Gemini should be useful for comparing agent behaviour, but the OpenAI provider remains the more trusted path until Gemini tool-call behaviour is validated.

---

## Local Provider

File:

```text
clients/providers/local_agent_client.py
```

Role:

```text
Experimental local/offline MCP-capable provider.
```

The local provider uses an OpenAI-compatible endpoint, usually through Ollama.

Example `.env` values:

```env
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5:1.5b
```

Run:

```powershell
python -m clients.providers.local_agent_client "Review my current grocery planning context and suggest useful next actions."
```

The local provider is useful for:

- cheap testing
- offline experimentation
- comparing local model responses
- learning how model quality affects agent behaviour

Limitations:

- local tool calling depends on the selected model
- small local models may not reliably select tools
- large MCP results may exceed what a small local model can handle well
- local runtime performance depends on CPU/GPU/NPU support

---

## Shared Client Modules

### `clients/shared/config.py`

Loads environment-driven client settings such as:

```text
GROCERY_MCP_URL
OPENAI_AGENT_MODEL
GEMINI_MODEL
LOCAL_LLM_BASE_URL
LOCAL_LLM_MODEL
GROCERY_AGENT_ALLOW_WRITES
GROCERY_AGENT_MAX_TOOL_ROUNDS
GROCERY_AGENT_MAX_RESULT_CHARS
```

### `clients/shared/instructions.py`

Stores shared grocery-agent instructions and write-safety guidance.

This keeps provider prompts consistent.

### `clients/shared/tool_policy.py`

Defines tool categories and exposed tool names.

Typical categories:

```text
read/review/draft tools
write tools
destructive tools
```

Default policy:

```text
Expose read/review/draft tools.
Hide write tools unless explicitly enabled.
```

### `clients/shared/mcp_helpers.py`

Contains reusable MCP helper logic such as:

- connecting to MCP
- calling tools safely
- applying default tool arguments
- compacting structured tool results

### `clients/shared/schema_adapters.py`

Converts MCP tool metadata into provider-specific schema shapes where needed.

This prevents each provider file from maintaining its own large copy of tool schemas.

### `clients/shared/tool_logging.py`

Prints visible tool-call information.

Tool visibility matters because this project is a learning-focused implementation and because writes should never feel hidden.

### `clients/shared/openai_agents_filter.py`

Builds OpenAI-specific MCP tool filtering from the shared policy.

This lets the OpenAI provider use the same allowed-tool policy as Gemini and local providers.

---

## Tool Safety Policy

By default, provider clients expose read/review/draft tools only.

Default tools include:

```text
search_inventory
get_recent_intake
get_daily_intake_summary
search_intake
review_planning_context
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
draft_restock_suggestions_tool
draft_meal_suggestions_tool
```

Write tools are hidden unless write mode is enabled.

Write mode can be enabled with:

```powershell
--allow-writes
```

or:

```env
GROCERY_AGENT_ALLOW_WRITES=true
```

Write tools include operations such as:

```text
add_inventory_item
update_inventory_item
remove_inventory_item
consume_inventory_item
add_intake_entry
add_intake_item
update_intake_entry
update_intake_item
remove_intake_entry
remove_intake_item
add_meal_with_items
add_meal_with_inventory_items
```

Destructive tools, especially remove tools, require extra care.

Important rule:

```text
Advice, review, meal suggestion, restock suggestion, and planning requests should not use write tools.
```

---

## Environment Setup

Create a private `.env` file:

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

The `.env` file must stay local.

Check before committing:

```powershell
git check-ignore -v .env
git ls-files .env
```

Expected:

```text
.env is ignored
.env is not tracked
```

---

## Recommended Run Order

### 1. Start the MCP server

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

### 2. Run the no-LLM smoke test

```powershell
python -m clients.mcp_smoke_client
```

### 3. Run a cheaper provider check

```powershell
python -m clients.providers.gemini_agent_client "Review my planning context."
```

or:

```powershell
python -m clients.providers.local_agent_client "Review my planning context."
```

### 4. Run the paid OpenAI provider check

```powershell
python -m clients.providers.openai_agent_client "Review my planning context."
```

This order reduces paid API misuse.

---

## Write-Mode Testing

Use write mode only for deliberate, reversible test records.

Example:

```powershell
python -m clients.providers.openai_agent_client --allow-writes "Add a test inventory item called Test Apples with quantity 1 each."
```

Then verify:

```powershell
python -m clients.providers.openai_agent_client "Search inventory for Test Apples."
```

Then remove by exact `stock_id`:

```powershell
python -m clients.providers.openai_agent_client --allow-writes "Remove the inventory item with stock_id inv_test_or_actual_id."
```

Do not use write mode for broad requests like:

```text
Clean up my inventory.
Fix my groceries.
Remove things I do not need.
```

Those requests are too ambiguous for safe mutation.

---

## Testing Strategy

### Unit tests

Run:

```powershell
pytest tests/clients -q
```

Unit tests should not require:

- OpenAI API key
- Gemini API key
- running Ollama
- running MCP server

They should cover:

- config defaults
- shared instructions
- tool allowlists
- write gating
- schema conversion
- MCP result formatting

### Compile check

Run:

```powershell
python -m compileall clients
```

### MCP smoke test

Requires the MCP server to be running:

```powershell
python -m clients.mcp_smoke_client
```

### Provider checks

Requires provider credentials or local runtime:

```powershell
python -m clients.providers.openai_agent_client "Review my planning context."
python -m clients.providers.gemini_agent_client "Review my planning context."
python -m clients.providers.local_agent_client "Review my planning context."
```

---

## Troubleshooting

### MCP smoke client cannot connect

Check that the server is running:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Confirm `.env`:

```env
GROCERY_MCP_URL=http://127.0.0.1:8000/mcp
```

The root URL may show `404 Not Found`. That is expected. The MCP endpoint is `/mcp`.

### Provider client cannot authenticate

Check that the provider key exists in `.env`:

```env
OPENAI_API_KEY=...
GEMINI_API_KEY=...
```

Do not print secret values in logs.

### Local provider does not work

Check that Ollama or the local OpenAI-compatible endpoint is running.

Example:

```powershell
ollama list
ollama run qwen2.5:1.5b "Reply with one short sentence."
```

Then confirm:

```env
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5:1.5b
```

### Agent does not call tools

Possible causes:

- request did not require tools
- tool policy filtered out the needed tool
- local model did not support tool calling well
- provider failed to understand the tool schema
- MCP server did not expose the expected tool

Start with `mcp_smoke_client.py` to confirm the server side first.

### Agent calls too many tools

Reduce:

```env
GROCERY_AGENT_MAX_TOOL_ROUNDS=2
```

Use more direct prompts during testing.

### Output is too long

Reduce:

```env
GROCERY_AGENT_MAX_RESULT_CHARS=4000
```

---

## Known Limitations

- OpenAI is the primary high-confidence provider, but it uses a paid API.
- Gemini is useful for comparison, but its tool behaviour should be validated against your project.
- Local models may not reliably perform multi-tool reasoning.
- Write mode is intentionally gated and should be tested cautiously.
- Client tests validate shared helper logic but do not replace MCP service-layer tests.
- The project still uses CSV-backed persistence.
- Production deployment is out of scope for this stage.

---

## Future Improvements

Potential future work:

- token and cost monitoring
- explicit user approval before write tool execution
- provider output quality comparison tests
- MCP prompt templates for common grocery workflows
- more detailed provider tracing
- local model fallback workflow where Python calls MCP deterministically and the local model summarizes
- richer planning workflows
- grocery list generation
- long-term user feedback and preference learning
