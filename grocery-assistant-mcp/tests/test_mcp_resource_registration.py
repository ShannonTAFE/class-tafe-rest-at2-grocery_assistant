from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.mcp_resources.inventory_resources import (
    register_inventory_resources,
)
from grocery_assistant_mcp.mcp_resources.intake_resources import (
    register_intake_resources,
)
from grocery_assistant_mcp.mcp_resources.food_waste_resources import (
    register_food_waste_resources,
)
from grocery_assistant_mcp.mcp_resources.register import register_resources
from grocery_assistant_mcp.stdio_server import create_mcp_server


def test_register_inventory_resources_can_be_called():
    mcp = FastMCP("Test Grocery Assistant")

    result = register_inventory_resources(mcp)

    assert result is None


def test_register_intake_resources_can_be_called():
    mcp = FastMCP("Test Grocery Assistant")

    result = register_intake_resources(mcp)

    assert result is None

def test_register_food_waste_resources_can_be_called():
    mcp = FastMCP("Test Grocery Assistant")

    result = register_food_waste_resources(mcp)

    assert result is None


def test_register_all_resources_can_be_called():
    mcp = FastMCP("Test Grocery Assistant")

    result = register_resources(mcp)

    assert result is None


def test_create_mcp_server_returns_fastmcp_instance():
    mcp = create_mcp_server()

    assert isinstance(mcp, FastMCP)