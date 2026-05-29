"""Simple Gemini grocery assistant client.

This file intentionally does not bridge Gemini to MCP tools. It is only for
Gemini API checks, prompt experiments, and response-quality comparison.

Use openai_agent_client.py for MCP tool-calling agent workflows.
Use mcp_smoke_client.py for deterministic MCP connectivity checks.
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_REQUEST = "Suggest one simple dinner using rice, chicken, and broccoli."

GEMINI_GROCERY_INSTRUCTION = """
You are a concise grocery assistant.
This standalone Gemini client does not have access to MCP tools or stored grocery records.
If the user asks about current inventory, intake history, or saved planning context,
explain that they should use the OpenAI MCP agent client or deterministic MCP smoke client.
""".strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a simple Gemini grocery client.")
    parser.add_argument(
        "request",
        nargs="*",
        help="Natural-language request to send to Gemini.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        help="Gemini model to use. Defaults to GEMINI_MODEL or project fallback.",
    )
    return parser


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()

    request = " ".join(args.request).strip() or DEFAULT_REQUEST

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    client = genai.Client()
    response = client.models.generate_content(
        model=args.model,
        contents=request,
        config=types.GenerateContentConfig(
            system_instruction=GEMINI_GROCERY_INSTRUCTION,
            temperature=0.3,
        ),
    )

    print(response.text or "")


if __name__ == "__main__":
    main()
