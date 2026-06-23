"""MCP server entrypoint shim so `python -m travel_concierge.mcp_server` works."""
from travel_concierge.mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run()
