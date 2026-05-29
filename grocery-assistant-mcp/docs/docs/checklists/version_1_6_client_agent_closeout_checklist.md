# Version 1.6 Client-Agent Integration Closeout Checklist

Use this checklist before committing the Version 1.6 client-agent integration work.

---

## 1. File Structure

Confirm the new client structure exists:

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
```

Confirm client tests exist:

```text
tests/
  clients/
    test_config_and_instructions.py
    test_mcp_helpers.py
    test_schema_adapters.py
    test_tool_policy.py
```

---

## 2. Removed or Archived Old Client Files

Remove old files if the new provider structure replaces them:

```powershell
git rm clients/grocery_agent_client.py
git rm clients/gemini_grocery_client.py
git rm clients/check_gemini_env.py
git rm clients/check_local_llm.py
```

`clients/check_env.py` may stay if you still want a dedicated environment sanity check.

---

## 3. Environment Safety

Confirm `.env` is ignored:

```powershell
git check-ignore -v .env
```

Confirm `.env` is not tracked:

```powershell
git ls-files .env
```

Expected:

```text
.env is ignored
.env is not tracked
```

Confirm `.env.example` contains placeholders only.

---

## 4. Static Checks

Run:

```powershell
python -m compileall clients
pytest tests/clients -q
```

Expected:

```text
client files compile
client unit tests pass
```

---

## 5. MCP Server Check

Start the MCP server:

```powershell
python -m grocery_assistant_mcp.streamable_http_server
```

Expected endpoint:

```text
http://127.0.0.1:8000/mcp
```

---

## 6. MCP Smoke Client

In another terminal, run:

```powershell
python -m clients.mcp_smoke_client
```

Expected:

```text
Connected to Grocery MCP server.
Available tools listed.
search_inventory summary printed.
```

Optional:

```powershell
python -m clients.mcp_smoke_client --show-resources --show-prompts
```

---

## 7. Provider Read-Only Checks

Run cheaper/non-paid checks first when available:

```powershell
python -m clients.providers.gemini_agent_client "Review my planning context."
python -m clients.providers.local_agent_client "Review my planning context."
```

Then run the paid OpenAI check:

```powershell
python -m clients.providers.openai_agent_client "Review my planning context."
```

Expected:

```text
Provider client runs from python -m.
Tool calls are visible when used.
Final response is printed.
No write tools are used for advice/review prompts.
```

---

## 8. Optional Reversible Write Check

Use only if you intentionally want to validate write mode.

Example:

```powershell
python -m clients.providers.openai_agent_client --allow-writes "Add a test inventory item called Test Apples with quantity 1 each."
```

Then search:

```powershell
python -m clients.providers.openai_agent_client "Search inventory for Test Apples."
```

Then remove by exact `stock_id`:

```powershell
python -m clients.providers.openai_agent_client --allow-writes "Remove the inventory item with stock_id <actual_stock_id>."
```

Expected:

```text
Write tools only become available with --allow-writes or GROCERY_AGENT_ALLOW_WRITES=true.
The test item can be added, found, and removed.
```

---

## 9. Documentation Checks

Confirm these files are updated or added:

```text
README.md
docs/docs/guides/client_agent_integration.md
docs/docs/checklists/version_1_6_client_agent_closeout_checklist.md
docs/docs/journals/development_journal.md
```

Optional archive:

```text
docs/docs/archive/client_agent/client_agent_integration_current_stage.md
```

---

## 10. Git Review

Run:

```powershell
git status
git diff --stat
git diff -- README.md
git diff -- docs/docs/guides/client_agent_integration.md
```

Check for:

```text
no secrets
no accidental .env
old obsolete client docs removed or archived
provider commands use python -m
write mode documented as explicit only
```

---

## 11. Suggested Commit

```powershell
git add README.md clients tests docs .env.example
git commit -m "Finalize client agent integration"
```

Then:

```powershell
git push
```

---

## Closeout Summary

Version 1.6 is ready to close when:

- client files compile
- client unit tests pass
- MCP smoke client succeeds
- at least one provider client succeeds
- OpenAI paid path is tested intentionally
- `.env` is ignored and untracked
- README documents the new client-agent capability
- dedicated client-agent guide is committed
