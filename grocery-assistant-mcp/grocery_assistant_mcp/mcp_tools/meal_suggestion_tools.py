from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from grocery_assistant_mcp.core.grocery_service import draft_meal_suggestions


def register_meal_suggestion_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def draft_meal_suggestions_tool(
        include_use_soon: Annotated[
            bool,
            Field(
                description=(
                    "Whether to prioritise meal opportunities that use items "
                    "approaching expiry. Usually leave true."
                )
            ),
        ] = True,
        include_inventory_based: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include general meal opportunities from currently "
                    "available inventory, even when no use-soon item is involved."
                )
            ),
        ] = True,
        include_gap_hints: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include low-stock or out-of-stock ingredient hints "
                    "that may improve a meal. These hints do not block the meal."
                )
            ),
        ] = True,
        max_suggestions: Annotated[
            int,
            Field(
                description=(
                    "Maximum number of meal suggestion drafts to return. "
                    "Use a small number such as 3 to 5 for normal assistant replies."
                )
            ),
        ] = 5,
        use_soon_days: Annotated[
            int,
            Field(
                description=(
                    "Number of days before expiry that should count as use-soon. "
                    "Default is 3."
                )
            ),
        ] = 3,
    ) -> dict:
        """
        Draft meal suggestions from current grocery inventory signals.

        Use this when the user asks what they could eat, what meals are possible,
        what should be used soon, or what meal ideas fit their current groceries.

        This tool does not modify inventory, intake, waste, or shopping-list records.
        It returns draft meal opportunities with reasons, confidence, priority,
        and optional low/out-of-stock ingredient hints.
        """
        return draft_meal_suggestions(
            include_use_soon=include_use_soon,
            include_inventory_based=include_inventory_based,
            include_gap_hints=include_gap_hints,
            max_suggestions=max_suggestions,
            use_soon_days=use_soon_days,
        )