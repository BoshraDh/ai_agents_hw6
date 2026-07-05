"""Shared FastMCP server construction, so the Cop/Thief server modules stay duplication-free."""

from fastmcp import FastMCP


def build_stub_server(name: str, ready_message: str) -> FastMCP:
    """Build a minimal FastMCP app exposing a single stub `ping` tool.

    Stage 2 only proves MCP transport works end-to-end on independent
    servers; real game-state and LLM-backed tools replace this stub
    starting Stage 3/5.
    """
    mcp: FastMCP = FastMCP(name)

    @mcp.tool()
    def ping() -> str:
        """Stub tool confirming this MCP server is reachable and responding."""
        return ready_message

    return mcp
