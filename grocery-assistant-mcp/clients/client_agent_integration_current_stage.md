# Client and Agent Integration — Current Stage Documentation

## Purpose

This document records the current client and agent integration stage for the Grocery Assistant MCP project.

The project has moved beyond MCP Inspector and curl-only testing. The current stage proves that a Python client can connect to the Grocery Assistant MCP server, discover available MCP tools, call those tools, and support agent-style workflows through OpenAI, Gemini, and local model experiments.

This documentation is intended to support the `client-agent-integration` branch and should be reviewed before merging the client work back into `main`.

---

## Current Branch Strategy

Client and agent work should now live on a dedicated feature branch:

```text
client-agent-integration
```

The intended branch structure is:

```text
main
  stable baseline before client/agent work

client-agent-integration
  MCP client setup
  OpenAI agent client
  Gemini client experiments
  local Ollama testing
  client safety and model configuration work
```

If client commits were accidentally made on `main`, the safe recovery approach is:

1. Create a feature branch from the current `main` state.
2. Push the feature branch.
3. Reset `main` to the commit before client work began.
4. Force-update GitHub `main` with `--force-with-lease`.
5. Continue all client work on `client-agent-integration`.

Example commands:

```powershell
git switch -c client-agent-integration
git push -u origin client-agent-integration

git switch main
git branch backup-main-before-client-reset
git reset --hard <commit-before-client-work>
git push --force-with-lease origin main
```

---

## Security and Environment Files

API keys must never be committed.

The private `.env` file should exist only locally:

```env
OPENAI_API_KEY=your_real_openai_key_here
GEMINI_API_KEY=your_real_gemini_key_here
GROCERY_MCP_URL=http://127.0.0.1:8000/mcp

OPENAI_AGENT_MODEL=gpt-5.4-nano
GEMINI_MODEL=gemini-2.5-flash
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5:1.5b
```

The committed `.env.example` should contain placeholders only:

```env
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROCERY_MCP_URL=http://127.0.0.1:8000/mcp

OPENAI_AGENT_MODEL=gpt-5.4-nano
GEMINI_MODEL=gemini-2.5-flash
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5:1.5b
```

The root `.gitignore` should include:

```gitignore
# Local secrets
.env
.env.*
!.env.example

# Virtual environments
.venv/
venv/
env/

# Python cache
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
```

Before each commit, run:

```powershell
git status
git diff
git check-ignore -v .env
git ls-files .env
```

Expected result:

```text
.env is ignored
.env is not tracked
.env.example may be committed
```

---

## Current Client Files

The current client integration work may include these files:

```text
clients/
  check_env.py
  mcp_smoke_client.py
  grocery_agent_client.py
  check_gemini_env.py
  gemini_grocery_client.py
  check_local_llm.py
```

### `clients/check_env.py`

Purpose:

- Confirms `.env` is loading.
- Confirms `OPENAI_API_KEY` and `GROCERY_MCP_URL` exist.
- Does not print the API key.

This file is useful for validating local configuration before testing clients.

### `clients/mcp_smoke_client.py`

Purpose:

- Deterministic MCP client.
- Connects directly to the running Grocery Assistant MCP server.
- Pings the server.
- Lists available tools/resources.
- Calls `search_inventory`.

This is the first proof that Python code can communicate with the MCP server.

Validated behaviour:

```text
Python client → MCP HTTP server → Grocery MCP tools → structured result
```

### `clients/grocery_agent_client.py`

Purpose:

- OpenAI Agents SDK client.
- Connects an OpenAI model to the Grocery MCP server.
- Allows natural-language requests to trigger MCP tool calls.
- Uses `.env` model configuration through `OPENAI_AGENT_MODEL`.

Current recommended model:

```env
OPENAI_AGENT_MODEL=gpt-5.4-nano
```

This model should be used for cheap wiring tests. Stronger models can be tested later when comparing recommendation quality.

### `clients/check_gemini_env.py`

Purpose:

- Confirms `GEMINI_API_KEY` exists.
- Sends a small request to Gemini.
- Does not print the API key.

This should be used before testing the full Gemini MCP client.

### `clients/gemini_grocery_client.py`

Purpose:

- Gemini API client for Grocery MCP experimentation.
- Uses Gemini function calling to choose MCP-backed tool calls.
- Initially started with read/review/draft tools only.
- Current development direction allows broader tool access, including write tools, as long as tool-call visibility is clear.

Important design principle:

```text
Development mode may allow writes,
but every selected tool name and argument set must be printed before execution.
```

### `clients/check_local_llm.py`

Purpose:

- Tests a local model through Ollama's OpenAI-compatible API.
- Intended for cheap/offline experimentation.
- Best suited for summarisation and prompt-style testing, not full autonomous tool reasoning.

Current recommended local model:

```env
LOCAL_LLM_MODEL=qwen2.5:1.5b
```

---

## MCP Server Requirement

Before running any client that calls MCP tools, the Grocery Assistant MCP server must be running.

Expected MCP URL:

```text
http://127.0.0.1:8000/mcp
```

This should match:

```env
GROCERY_MCP_URL=http://127.0.0.1:8000/mcp
```

The server should expose tools such as:

```text
search_inventory
add_inventory_item
update_inventory_item
remove_inventory_item
get_recent_intake
get_daily_intake_summary
add_intake_entry
add_intake_item
update_intake_entry
update_intake_item
remove_intake_entry
remove_intake_item
search_intake
consume_inventory_item
add_intake_item_from_inventory
add_meal_with_items
add_meal_with_inventory_items
review_planning_context
review_low_stock_items
review_use_soon_items
review_inventory_data_quality
draft_restock_suggestions_tool
draft_meal_suggestions_tool
```

---

## Validated MCP Smoke Test

The deterministic smoke client has successfully connected to the MCP server and listed the available Grocery Assistant tools.

Example command:

```powershell
python clients/mcp_smoke_client.py
```

Expected output pattern:

```text
Connected to Grocery MCP server.

Available tools:
- search_inventory
- add_inventory_item
- update_inventory_item
...

search_inventory result:
CallToolResult(...)
```

The result confirms:

```text
Python MCP client can connect to the server.
The server exposes the expected grocery tools.
The client can call search_inventory.
The tool returns structured inventory data.
```

Recommended improvement:

The smoke client should print a compact inventory summary instead of the full inventory payload.

Suggested output shape:

```text
search_inventory summary:
- Returned 36 inventory item(s)
- inv_001: Spaghetti (in_stock)
- inv_002: Beef mince (in_stock)
- inv_003: Tomato pasta sauce (in_stock)
```

---

## OpenAI Agent Client

The OpenAI agent client represents the first full agent integration path.

Flow:

```text
User natural language request
  ↓
grocery_agent_client.py
  ↓
OpenAI agent
  ↓
MCP server tool discovery
  ↓
Grocery MCP tool call
  ↓
Structured result
  ↓
Agent response
```

Example command:

```powershell
python clients/grocery_agent_client.py "Review my current inventory and suggest what meals I should make soon."
```

Observed successful behaviour:

- Agent reviewed inventory.
- Agent used meal-suggestion signals.
- Agent identified use-soon items.
- Agent produced meal suggestions based on current inventory.

Recommended model configuration:

```python
OPENAI_AGENT_MODEL = os.getenv("OPENAI_AGENT_MODEL", "gpt-5.4-nano")
```

Recommended `.env` value for cheap testing:

```env
OPENAI_AGENT_MODEL=gpt-5.4-nano
```

Recommended `.env` value for better quality development testing:

```env
OPENAI_AGENT_MODEL=gpt-5.4-mini
```

---

## OpenAI Agent Safety Guidance

The agent should include explicit write-safety guidance in its instructions:

```text
WRITE SAFETY:
- Never call add, update, remove, or consume tools unless the user explicitly asks to change stored data.
- If the user asks for advice, review, suggestions, planning, or recommendations, use read/review/draft tools only.
- If the user request is ambiguous, prefer explaining what could be changed rather than changing data.
- Removal tools are destructive. Only use remove tools when the user clearly asks to delete/remove a record.
```

This keeps the agent aligned with the project design:

```text
Backend MCP tools = deterministic execution
Agent = reasoning, interpretation, orchestration
```

---

## Gemini API Client

The Gemini client is being used as a second agent/model comparison path.

Initial purpose:

```text
Gemini user request
  ↓
Gemini chooses an MCP tool
  ↓
Python client calls Grocery MCP server
  ↓
Tool result returns to Gemini
  ↓
Gemini writes final answer
```

The Gemini client was initially restricted to read/review/draft tools. This was a safety choice while validating function calling.

Current development goal:

- Allow broader access to inventory and intake write tools.
- Make all tool calls clearly visible in the terminal.
- Print selected tool name and arguments before execution.
- Keep destructive operations visible and intentional.

Recommended terminal printout for tool calls:

```python
print("\n" + "=" * 72)
print("GEMINI TOOL CALL")
print("=" * 72)
print(f"Tool: {tool_name}")
print("Arguments:")
print(json.dumps(tool_args, indent=2, ensure_ascii=False))
print("=" * 72)
```

Recommended Gemini system guidance:

```text
WRITE TOOL VISIBILITY:
- You are allowed to use write tools when the user's request clearly asks to add, update, consume, or remove stored data.
- Tool calls must be interpretable. The client will print selected tool names and arguments before execution.
- Do not call write tools for advice-only requests.
- For advice, review, meal suggestions, restock suggestions, or planning, prefer review/draft tools.
- If using a write tool, explain afterward what was changed and which tool was used.
- Use remove tools only when the user clearly asks to delete or remove a stored record.
- If a request is ambiguous, do not write. Explain what could be changed instead.
```

---

## Gemini Tool Access Policy

For current development, a practical tool set is:

```python
ALLOWED_MCP_TOOLS = {
    # Inventory
    "search_inventory",
    "add_inventory_item",
    "update_inventory_item",
    "remove_inventory_item",
    "consume_inventory_item",

    # Intake
    "get_recent_intake",
    "get_daily_intake_summary",
    "search_intake",
    "add_intake_entry",
    "add_intake_item",
    "update_intake_entry",
    "update_intake_item",
    "remove_intake_entry",
    "remove_intake_item",

    # Planning / recommendations
    "review_planning_context",
    "review_low_stock_items",
    "review_use_soon_items",
    "review_inventory_data_quality",
    "draft_restock_suggestions_tool",
    "draft_meal_suggestions_tool",
}
```

Batch tools should be added only after their exact schemas are confirmed:

```text
add_intake_item_from_inventory
add_meal_with_items
add_meal_with_inventory_items
```

Reason:

```text
Gemini function declarations require explicit argument schemas.
Complex batch tools should not be guessed manually.
```

---

## Local Model / Ollama Experiment

The local model path is useful for cheap/offline testing, but it is not currently the recommended path for full autonomous agent workflows.

Recommended model test:

```powershell
ollama pull qwen2.5:1.5b
ollama run qwen2.5:1.5b "Reply with one short sentence only: local model is working."
```

Recommended `.env` local configuration:

```env
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5:1.5b
```

Local model role:

```text
Good for:
- summarising MCP outputs
- offline prompt experiments
- cheap natural language explanations

Not ideal yet for:
- full multi-tool agent reasoning
- large inventory context
- complex recommendation planning
```

Recommended local architecture:

```text
Python calls MCP tool deterministically
  ↓
Python sends compact result to local model
  ↓
Local model summarises or explains result
```

This avoids relying on fragile local tool-calling.

---

## NPU / Local Acceleration Notes

The user's laptop may have an NPU, especially on Snapdragon X / Copilot+ PC hardware.

However:

```text
Having an NPU does not mean Ollama automatically uses it.
```

Current practical diagnosis:

1. Open Task Manager.
2. Watch CPU, Memory, GPU, and NPU.
3. Run a small Ollama prompt.
4. If CPU spikes and NPU stays idle, Ollama is not using the NPU path.

There is currently no simple project-level setting such as:

```text
OLLAMA_USE_NPU=true
```

For this project, the local model path should remain experimental.

---

## Recommended Manual Test Checklist

### 1. Environment safety

```powershell
git check-ignore -v .env
git ls-files .env
```

Expected:

```text
.env is ignored
.env is not tracked
```

### 2. MCP smoke client

```powershell
python clients/mcp_smoke_client.py
```

Expected:

```text
Connected to Grocery MCP server.
Available tools listed.
search_inventory returns data.
```

### 3. OpenAI agent client

```powershell
python clients/grocery_agent_client.py "What items should I use soon?"
```

Expected:

```text
Agent uses review/use-soon or meal suggestion tools.
Agent explains recommendations.
No write tools called for advice-only request.
```

### 4. Gemini environment

```powershell
python clients/check_gemini_env.py
```

Expected:

```text
Gemini responds with a short confirmation.
No key is printed.
```

### 5. Gemini MCP client read test

```powershell
python clients/gemini_grocery_client.py "Review my low stock items and explain what is urgent versus optional."
```

Expected:

```text
Visible tool call output.
Low-stock review response.
No write tools unless explicitly requested.
```

### 6. Gemini low-risk write test

Use a reversible test item:

```powershell
python clients/gemini_grocery_client.py "Add test item called Test Apples, brand Test Brand, category fruit, location fridge, quantity 1, unit each, servings 1, expiry date 2026-06-01, with note Gemini write test."
```

Expected:

```text
GEMINI TOOL CALL
Tool: add_inventory_item
Arguments: visible JSON
```

Then verify and remove:

```powershell
python clients/gemini_grocery_client.py "Search inventory for Test Apples."
python clients/gemini_grocery_client.py "Remove the inventory item for Test Apples."
```

If removal requires `stock_id`, search first and remove by exact `stock_id`.

### 7. Local model smoke test

```powershell
python clients/check_local_llm.py
```

Expected:

```text
Local model returns a short answer through Ollama API.
```

---

## Current Recommended Development Scope

This stage should remain focused on client integration and observability.

In scope:

```text
- Python MCP smoke client
- OpenAI agent client
- Gemini comparison client
- local model smoke testing
- model selection through .env
- safe API key handling
- visible tool-call logging
- manual test checklist
- branch separation
```

Out of scope for this stage:

```text
- silent autonomous writes
- production deployment
- full NPU optimisation
- training a custom model
- complex local tool-calling agent
- automatic long-term learning pipeline
```

---

## Suggested Version Label

This work can be tracked as:

```text
Version 1.6 — Client and Agent Integration
```

Suggested sub-stages:

```text
1.6A — deterministic MCP client
1.6B — OpenAI agent client
1.6C — Gemini comparison client
1.6D — local model fallback experiment
1.6E — docs, branch cleanup, safety checklist
```

---

## Final Current-State Summary

The current stage has successfully proven that the Grocery Assistant MCP project can be accessed through a Python client and through an agent-style interface.

The strongest validated path is:

```text
OpenAI agent client → Grocery MCP server → recommendation/review tools → natural-language answer
```

The Gemini path is actively being expanded for comparison testing, with emphasis on tool-call visibility and controlled write access.

The local model path is useful as a low-cost experimental fallback, but should be limited to small summarisation workflows until performance and acceleration are better understood.

The next best engineering step is to keep all work on `client-agent-integration`, finish the client documentation and manual test checklist, then open a Pull Request from:

```text
client-agent-integration → main
```

Do not merge until the branch review confirms that `.env` is not tracked and client behaviour is sufficiently tested.
