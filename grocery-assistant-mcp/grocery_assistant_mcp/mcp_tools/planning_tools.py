"""MCP planning tools for Grocery Assistant MCP Version 1.5."""

from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from grocery_assistant_mcp.core.planning_service import (
    build_planning_context,
    review_low_stock_items as review_low_stock_items_service,
    review_use_soon_items as review_use_soon_items_service,
)


def register_planning_tools(mcp: FastMCP) -> None:
    """Register read-only planning tools."""

    @mcp.tool()
    def review_planning_context(
        recent_days: Annotated[
            int,
            Field(
                description=(
                    "Number of recent days of intake history to consider for planning context. "
                    "Use 7 for a normal weekly review. Values are clamped between 1 and 90."
                )
            ),
        ] = 7,
        include_inventory: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include inventory-derived planning signals such as available, "
                    "low-stock, out-of-stock, expired, and use-soon items."
                )
            ),
        ] = True,
        include_recent_intake: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include recent-intake signals so the agent can avoid overclaiming "
                    "about meal repetition or recent eating patterns."
                )
            ),
        ] = True,
        include_consumption: Annotated[
            bool,
            Field(
                description=(
                    "Reserved for later Version 1.5 consumption-pattern signals. "
                    "In 1.5A this only returns a warning that consumption signals are not implemented."
                )
            ),
        ] = False,
        include_waste: Annotated[
            bool,
            Field(
                description=(
                    "Reserved for later Version 1.5 waste-pattern signals. "
                    "In 1.5A this only returns a warning that waste signals are not implemented."
                )
            ),
        ] = False,
    ) -> dict:
        """
        Build a read-only planning context from inventory and recent intake records.

        This tool prepares structured signals, warnings, next actions, and safety
        metadata for the connected LLM agent. It does not mutate any records.
        """
        return build_planning_context(
            recent_days=recent_days,
            include_inventory=include_inventory,
            include_recent_intake=include_recent_intake,
            include_consumption=include_consumption,
            include_waste=include_waste,
        )

    @mcp.tool()
    def review_low_stock_items(
        include_low: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include inventory signals where stock_status is low."
                )
            ),
        ] = True,
        include_very_low: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include inventory signals where stock_status is very_low."
                )
            ),
        ] = True,
        include_out: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include inventory signals where stock_status is out."
                )
            ),
        ] = True,
    ) -> dict:
        """
        Return a read-only focused review of low, very-low, and out-of-stock inventory items.

        This tool reuses the planning signal layer. It does not update inventory,
        create shopping-list records, deduct stock, or save recommendations.
        """
        return review_low_stock_items_service(
            include_low=include_low,
            include_very_low=include_very_low,
            include_out=include_out,
        )

    @mcp.tool()
    def review_use_soon_items(
        include_use_soon: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include usable inventory items that expire within the use-soon window."
                )
            ),
        ] = True,
        include_expired: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include inventory items marked expired or with an expiry date in the past."
                )
            ),
        ] = True,
        include_no_expiry_data: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include data-quality signals for inventory items missing expiry dates."
                )
            ),
        ] = True,
        include_invalid_expiry_date: Annotated[
            bool,
            Field(
                description=(
                    "Whether to include data-quality signals for inventory items with invalid expiry dates."
                )
            ),
        ] = True,
    ) -> dict:
        """
        Return a read-only focused review of use-soon, expired, and expiry-data inventory items.

        This tool reuses the planning signal layer. It does not update inventory,
        create waste records, deduct stock, or save recommendations.
        """
        return review_use_soon_items_service(
            include_use_soon=include_use_soon,
            include_expired=include_expired,
            include_no_expiry_data=include_no_expiry_data,
            include_invalid_expiry_date=include_invalid_expiry_date,
        )

