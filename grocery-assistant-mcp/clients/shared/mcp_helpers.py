"""Shared MCP helper functions for provider clients."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


from clients.shared.tool_policy import is_tool_allowed, merge_default_args
from clients.shared.tool_logging import print_tool_call


@dataclass(frozen=True)
class MCPToolInfo:
    """Provider-neutral representation of an MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]


def _get_attr_or_key(obj: Any, attr: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


def _normalise_schema(schema: Any) -> dict[str, Any]:
    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}, "required": []}

    normalised = dict(schema)
    normalised.setdefault("type", "object")
    normalised.setdefault("properties", {})
    normalised.setdefault("required", [])
    return normalised


def tool_info_from_mcp_tool(tool: Any) -> MCPToolInfo:
    """Convert a FastMCP/MCP tool object into a small stable shape."""

    name = _get_attr_or_key(tool, "name", "")
    description = _get_attr_or_key(tool, "description", "") or "Grocery MCP tool."

    schema = (
        _get_attr_or_key(tool, "inputSchema")
        or _get_attr_or_key(tool, "input_schema")
        or _get_attr_or_key(tool, "parameters")
        or {}
    )

    return MCPToolInfo(
        name=str(name),
        description=str(description),
        input_schema=_normalise_schema(schema),
    )


def filter_mcp_tools(tools: list[Any], *, allow_writes: bool) -> list[MCPToolInfo]:
    """Apply the project tool policy to MCP server tools."""

    result: list[MCPToolInfo] = []
    for tool in tools:
        info = tool_info_from_mcp_tool(tool)
        if info.name and is_tool_allowed(info.name, allow_writes=allow_writes):
            result.append(info)
    return result


def compact_tool_result(result: Any, *, max_chars: int = 8000) -> str:
    """Convert an MCP tool result to compact JSON/text for a model."""

    structured = getattr(result, "structured_content", None)
    if structured is None and isinstance(result, dict):
        structured = result.get("structured_content")

    if structured is not None:
        text = json.dumps(structured, indent=2, ensure_ascii=False)
    else:
        text = str(result)

    if len(text) > max_chars:
        return text[:max_chars] + "\n... [tool result truncated]"
    return text


async def call_mcp_tool_checked(
    mcp_client: Any,
    tool_name: str,
    args: dict[str, Any] | None,
    *,
    provider_name: str,
    allow_writes: bool,
    max_result_chars: int = 8000,
) -> str:
    """Policy-check, log, call an MCP tool, and return compact text."""

    if not is_tool_allowed(tool_name, allow_writes=allow_writes):
        raise ValueError(
            f"Tool '{tool_name}' is not allowed in this client run. "
            f"Run with --allow-writes only for explicit write testing."
        )

    safe_args = merge_default_args(tool_name, args)
    print_tool_call(provider_name=provider_name, tool_name=tool_name, tool_args=safe_args)
    result = await mcp_client.call_tool(tool_name, safe_args)
    return compact_tool_result(result, max_chars=max_result_chars)
