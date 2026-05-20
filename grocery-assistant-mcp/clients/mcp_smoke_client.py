import asyncio
import os
from dotenv import load_dotenv
from fastmcp import Client


load_dotenv()

MCP_URL = os.getenv("GROCERY_MCP_URL", "http://127.0.0.1:8000/mcp")


async def main() -> None:
    client = Client(MCP_URL)

    async with client:
        await client.ping()

        print("Connected to Grocery MCP server.")

        tools = await client.list_tools()

        print("\nAvailable tools:")
        for tool in tools:
            print(f"- {tool.name}")

        result = await client.call_tool(
            "search_inventory",
            {
                "query": "",
                "category": "",
                "location": "",
            },
        )

        items = result.structured_content.get("result", [])

        print("\nsearch_inventory summary:")
        print(f"- Returned {len(items)} inventory item(s)")

        for item in items[:5]:
            print(
                f"- {item.get('stock_id')}: "
                f"{item.get('food_item')} "
                f"({item.get('stock_status')})"
            )

if __name__ == "__main__":
    asyncio.run(main())