"""MCP planning tools for Grocery Assistant MCP Version 1.5A."""

from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from grocery_assistant_mcp.core.planning_service import build_planning_context


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
