"""Convert MCP tool schemas into provider-specific tool declaration formats."""

from __future__ import annotations

from typing import Any

from clients.shared.mcp_helpers import MCPToolInfo


def to_openai_chat_tool(tool: MCPToolInfo) -> dict[str, Any]:
    """Convert an MCP tool to an OpenAI-compatible chat completions tool."""

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


def to_openai_chat_tools(tools: list[MCPToolInfo]) -> list[dict[str, Any]]:
    return [to_openai_chat_tool(tool) for tool in tools]


def to_gemini_function_declarations(tools: list[MCPToolInfo]) -> list[Any]:
    """Convert MCP tools to Gemini FunctionDeclaration objects.

    The import is local so unit tests for shared helpers do not require the
    Gemini package unless this adapter is actually used.
    """

    from google.genai import types

    return [
        types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=tool.input_schema,
        )
        for tool in tools
    ]


def to_gemini_tools(tools: list[MCPToolInfo]) -> list[Any]:
    from google.genai import types

    function_declarations = to_gemini_function_declarations(tools)
    if not function_declarations:
        return []
    return [types.Tool(function_declarations=function_declarations)]
