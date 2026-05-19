# Register Planning Tools Patch Note

Add the planning tool registration to your existing MCP tools register file.

Your project likely has something like:

```python
from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.mcp_tools.inventory_tools import register_inventory_tools
from grocery_assistant_mcp.mcp_tools.intake_tools import register_intake_tools


def register_tools(mcp: FastMCP) -> None:
    register_inventory_tools(mcp)
    register_intake_tools(mcp)
```

Update it to include:

```python
from grocery_assistant_mcp.mcp_tools.planning_tools import register_planning_tools
```

and inside `register_tools`:

```python
register_planning_tools(mcp)
```

The MCP wrapper is intentionally thin. Business logic stays in:

```text
grocery_assistant_mcp/core/planning_service.py
```
