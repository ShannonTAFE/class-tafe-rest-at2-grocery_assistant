from grocery_assistant_mcp.server_factory import create_mcp_server


HOST = "127.0.0.1"
PORT = 8000
MOUNT_PATH = "/mcp"


mcp = create_mcp_server(
    host=HOST,
    port=PORT,
)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        mount_path=MOUNT_PATH,
    )