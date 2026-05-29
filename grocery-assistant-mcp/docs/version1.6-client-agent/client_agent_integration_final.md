# Client and Agent Integration — Finalized Provider Client Structure

## Purpose

This document finalizes the client-agent integration direction for the Grocery Assistant MCP project.

The client layer now has a clearer responsibility:

```text
MCP server
  = deterministic grocery tools, resources, records, and business logic

Provider client
  = connects one model/provider to the MCP server

Agent/model
  = interprets the user request, decides when tools are useful, and explains results
```

The final direction is to keep OpenAI, Gemini, and local LLM clients in the same provider-client structure while acknowledging that each provider uses a different implementation internally.

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

## What Changed

### Removed old distracting split

The older direction separated providers like this:

```text
OpenAI = real MCP agent
Gemini = prompt-only comparison
Local = prompt-only comparison
```

That made provider comparison unfair because OpenAI had live MCP access while Gemini/local did not.

### New direction

The finalized direction is:

```text
OpenAI provider client
  = MCP-capable agent client through the OpenAI Agents SDK

Gemini provider client
  = MCP-capable agent client through Gemini function calling and shared MCP helpers

Local provider client
  = MCP-capable experimental agent client through an OpenAI-compatible tool-calling API
```

This gives each provider the same high-level role:

```text
Natural language request
  -> provider model
  -> MCP tool selection or direct answer
  -> MCP server tool call when needed
  -> final explanation
```

---

## Provider Capabilities

| Client | MCP-connected | Tool selection | Recommended use | Confidence |
|---|---:|---:|---|---|
| `mcp_smoke_client.py` | Yes | No | Server connectivity test | High |
| `providers/openai_agent_client.py` | Yes | Yes, via OpenAI Agents SDK | Primary agent path | High |
| `providers/gemini_agent_client.py` | Yes | Yes, via Gemini function calling | Free-tier comparison agent | Medium |
| `providers/local_agent_client.py` | Yes | Yes, if local model supports tools | Offline/cheap experiment | Experimental |

---

## Why OpenAI Remains Primary

OpenAI remains the primary provider because it has the cleanest MCP integration path through the Agents SDK.

It should be used for the most realistic end-to-end test of:

```text
User request -> model reasoning -> MCP tools -> final answer
```

Because it uses a paid API, it should not be the only validation path. Use deterministic smoke tests and cheaper providers before running repeated OpenAI calls.

---

## Why Gemini Is Reintroduced as an MCP-Capable Client

The old `gemini_grocery_client.py` did too much in one file:

```text
env loading
manual schemas
MCP allowlist
Gemini function declarations
function-call extraction
MCP tool execution
result compaction
final response generation
```

The new `gemini_agent_client.py` keeps only provider-specific Gemini behavior in the provider file. Shared MCP policy, schema conversion, logging, and result compaction now live under `clients/shared/`.

This keeps Gemini useful as a free-tier comparison path without recreating a giant all-in-one client file.

---

## Why Local LLM Is Still Experimental

The local provider has the same outer shape, but local tool-calling depends heavily on the selected model and local runtime.

The local client is useful for:

```text
- low-cost testing
- offline experimentation
- comparing local model behavior
- checking whether local tool calling is viable
```

It should not be treated as equally reliable as OpenAI until local tool-calling behavior is validated with your chosen model.

---

## Tool Safety Policy

By default, provider clients expose only read/review/draft tools.

Default exposed tools include:

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

Write tools are hidden unless explicitly enabled:

```powershell
--allow-writes
```

or:

```env
GROCERY_AGENT_ALLOW_WRITES=true
```

Write tools include add/update/remove/consume/logging workflows.

This protects normal agent testing from accidental data mutation.

---

## Recommended Commands

Run from the project root.

### 1. Deterministic MCP smoke test

```powershell
python -m clients.mcp_smoke_client
```

Optional:

```powershell
python -m clients.mcp_smoke_client --show-resources --show-prompts
```

### 2. OpenAI provider agent

```powershell
python -m clients.providers.openai_agent_client "What items should I use soon?"
```

### 3. Gemini provider agent

```powershell
python -m clients.providers.gemini_agent_client "What items should I use soon?"
```

### 4. Local provider agent

```powershell
python -m clients.providers.local_agent_client "What items should I use soon?"
```

### 5. Explicit write-mode test

Use this only for reversible development testing:

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

---

## Environment Variables

Private `.env` example:

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

---

## Testing Plan

Run fast unit tests:

```powershell
pytest tests/clients
```

Run smoke client with MCP server running:

```powershell
python -m clients.mcp_smoke_client
```

Run read-only provider checks:

```powershell
python -m clients.providers.openai_agent_client "Review my planning context."
python -m clients.providers.gemini_agent_client "Review my planning context."
python -m clients.providers.local_agent_client "Review my planning context."
```

For the paid OpenAI path, test only after smoke and cheaper provider tests are working.

---

## Suggested Cleanup

Remove older client files if they still exist:

```powershell
git rm clients/grocery_agent_client.py
git rm clients/gemini_grocery_client.py
git rm clients/check_gemini_env.py
git rm clients/check_local_llm.py
```

Keep `check_env.py` only if you still want a dedicated environment sanity check. Otherwise, the provider clients themselves will fail clearly when required environment variables are missing.

---

## Final Commit Checklist

```powershell
python -m compileall clients
pytest tests/clients
python -m clients.mcp_smoke_client

git status
git check-ignore -v .env
git ls-files .env
```

Expected:

```text
.env is ignored
.env is not tracked
unit tests pass
MCP smoke test connects
provider clients run from python -m
```

Suggested commit:

```powershell
git add clients tests docs
git commit -m "Finalize provider agent clients"
```

---

## Final Summary

This version finalizes the client-agent layer around one clear idea:

```text
Same Grocery MCP server.
Same client safety policy.
Same terminal-facing provider structure.
Different model/provider quality.
```

OpenAI remains the primary high-confidence agent path. Gemini becomes a useful free-tier MCP-capable comparison path. Local LLM becomes an experimental MCP-capable path for offline and low-cost testing.
