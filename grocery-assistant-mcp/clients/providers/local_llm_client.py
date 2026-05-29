"""Simple local LLM grocery assistant client through an OpenAI-compatible API.

Designed for Ollama or another local OpenAI-compatible endpoint. This client does
not call MCP tools directly. Use it for cheap/offline prompt experiments or for
summarising text that Python has already retrieved deterministically.
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI


DEFAULT_LOCAL_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_LOCAL_MODEL = "qwen2.5:1.5b"
DEFAULT_REQUEST = "Suggest one simple dinner using rice, chicken, and broccoli."

LOCAL_GROCERY_SYSTEM_PROMPT = """
You are a concise grocery assistant.
This local client does not have direct access to MCP tools or saved grocery records.
Be clear when you are giving general advice rather than using live project data.
""".strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a simple local LLM grocery client.")
    parser.add_argument(
        "request",
        nargs="*",
        help="Natural-language request to send to the local model.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("LOCAL_LLM_BASE_URL", DEFAULT_LOCAL_BASE_URL),
        help="OpenAI-compatible local API base URL.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("LOCAL_LLM_MODEL", DEFAULT_LOCAL_MODEL),
        help="Local model name. Defaults to LOCAL_LLM_MODEL or project fallback.",
    )
    return parser


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()

    request = " ".join(args.request).strip() or DEFAULT_REQUEST

    client = OpenAI(
        base_url=args.base_url,
        api_key=os.getenv("LOCAL_LLM_API_KEY", "ollama"),
    )

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": LOCAL_GROCERY_SYSTEM_PROMPT},
            {"role": "user", "content": request},
        ],
        temperature=0.3,
    )

    print(response.choices[0].message.content or "")


if __name__ == "__main__":
    main()
