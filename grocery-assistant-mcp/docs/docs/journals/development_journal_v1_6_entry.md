## Version 1.6 — Client and Agent Integration

Focus:

```text
Finalize provider-agent clients for OpenAI, Gemini, and local LLM access to the Grocery Assistant MCP server.
```

Key outcomes:

- Added a deterministic Python MCP smoke client for no-LLM server connectivity testing.
- Reorganized client code around provider clients under `clients/providers/`.
- Added shared client utilities under `clients/shared/`.
- Clarified that the MCP server remains the source of truth for grocery tools, records, validation, and business logic.
- Kept OpenAI as the primary high-confidence MCP agent path.
- Added Gemini as an MCP-capable comparison provider using a smaller provider-client structure.
- Added a local OpenAI-compatible provider client for experimental local/offline model testing.
- Added a shared tool safety policy.
- Defaulted provider clients to read/review/draft tools only.
- Added explicit write-mode gating through `--allow-writes` or `GROCERY_AGENT_ALLOW_WRITES=true`.
- Added visible tool-call logging for interpretability.
- Added tests for shared client policy, config, schema adaptation, and MCP result formatting.
- Updated root README and client-agent documentation to treat agent integration as a current capability rather than a future direction.

Important design decision:

```text
Provider clients should share the same outer structure and safety policy, while each provider can use different internal mechanics.
```

The intended comparison target is now:

```text
Same MCP server
Same grocery tool policy
Same terminal-facing client structure
Different model/provider quality, cost, speed, and reliability
```

OpenAI paid usage note:

```text
Use deterministic MCP smoke tests and cheaper provider checks first. Run the paid OpenAI provider intentionally after the server and shared client layer are working.
```

Validation checklist:

```powershell
python -m compileall clients
pytest tests/clients -q
python -m clients.mcp_smoke_client
python -m clients.providers.gemini_agent_client "Review my planning context."
python -m clients.providers.local_agent_client "Review my planning context."
python -m clients.providers.openai_agent_client "Review my planning context."
```

Suggested commit:

```powershell
git add README.md clients tests docs .env.example
git commit -m "Finalize client agent integration"
```
