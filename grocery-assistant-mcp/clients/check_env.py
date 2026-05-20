import os
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    mcp_url = os.getenv("GROCERY_MCP_URL")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing from .env")

    if not mcp_url:
        raise RuntimeError("GROCERY_MCP_URL is missing from .env")

    print("OPENAI_API_KEY is loaded safely.")
    print(f"GROCERY_MCP_URL={mcp_url}")


if __name__ == "__main__":
    main()