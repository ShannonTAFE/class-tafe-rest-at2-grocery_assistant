"""Shared CLI helpers for provider clients."""

from __future__ import annotations

import argparse
import os

from clients.shared.config import DEFAULT_MCP_URL, DEFAULT_REQUEST, env_bool, env_str


def add_common_agent_args(
    parser: argparse.ArgumentParser,
    *,
    default_model_env: str,
    default_model: str,
) -> argparse.ArgumentParser:
    parser.add_argument(
        "request",
        nargs="*",
        help="Natural-language request to send to the grocery agent.",
    )
    parser.add_argument(
        "--model",
        default=env_str(default_model_env, default_model),
        help=f"Model to use. Defaults to {default_model_env} or {default_model!r}.",
    )
    parser.add_argument(
        "--mcp-url",
        default=env_str("GROCERY_MCP_URL", DEFAULT_MCP_URL),
        help="Grocery MCP Streamable HTTP URL.",
    )
    parser.add_argument(
        "--allow-writes",
        action="store_true",
        default=env_bool("GROCERY_AGENT_ALLOW_WRITES", default=False),
        help="Expose write tools for explicit development testing. Default: false.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("GROCERY_MCP_TIMEOUT", "30")),
        help="MCP server timeout in seconds.",
    )
    parser.add_argument(
        "--max-tool-rounds",
        type=int,
        default=int(os.getenv("GROCERY_AGENT_MAX_TOOL_ROUNDS", "4")),
        help="Maximum model/tool loop rounds for manual provider clients.",
    )
    parser.add_argument(
        "--max-result-chars",
        type=int,
        default=int(os.getenv("GROCERY_AGENT_MAX_RESULT_CHARS", "8000")),
        help="Maximum characters of each MCP result sent back to the model.",
    )
    return parser


def request_from_args(request_parts: list[str]) -> str:
    return " ".join(request_parts).strip() or DEFAULT_REQUEST
