"""OpenAI Agents SDK MCP tool-filter helper.

Kept separate so importing shared policy/tests does not require the Agents SDK.
"""

from __future__ import annotations

from clients.shared.tool_policy import allowed_tool_names


def build_static_tool_filter(*, allow_writes: bool):
    """Create a static MCP tool filter for OpenAI Agents SDK servers."""

    from agents.mcp import create_static_tool_filter

    return create_static_tool_filter(
        allowed_tool_names=sorted(allowed_tool_names(allow_writes=allow_writes))
    )
