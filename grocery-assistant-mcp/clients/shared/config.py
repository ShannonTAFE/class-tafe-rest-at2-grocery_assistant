"""Shared configuration for Grocery Assistant provider clients."""

from __future__ import annotations

import os


DEFAULT_MCP_URL = "http://127.0.0.1:8000/mcp"
DEFAULT_OPENAI_AGENT_MODEL = "gpt-5.4-mini"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_LOCAL_LLM_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_LOCAL_LLM_MODEL = "qwen2.5:1.5b"
DEFAULT_REQUEST = "Review my current grocery planning context and suggest useful next actions."


def env_bool(name: str, *, default: bool = False) -> bool:
    """Read a boolean-like environment variable safely."""

    raw = os.getenv(name)
    if raw is None:
        return default

    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_str(name: str, default: str) -> str:
    """Read a string environment variable with a non-empty fallback."""

    value = os.getenv(name, "").strip()
    return value or default
