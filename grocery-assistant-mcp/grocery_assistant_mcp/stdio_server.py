from grocery_assistant_mcp.server_factory import create_mcp_server


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run()