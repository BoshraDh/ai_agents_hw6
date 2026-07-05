"""FastMCP server hosting the Thief agent (Stage 2: transport skeleton, stub tool only)."""

from cop_thief_mcp.servers.common import build_stub_server
from cop_thief_mcp.shared.mcp_config import load_mcp_servers_config

mcp = build_stub_server(name="thief-server", ready_message="thief-server-ready")


def main() -> None:  # pragma: no cover - process entry point, exercised manually/in integration
    endpoint = load_mcp_servers_config().thief_server
    mcp.run(transport="http", host=endpoint.host, port=endpoint.port)


if __name__ == "__main__":  # pragma: no cover
    main()
