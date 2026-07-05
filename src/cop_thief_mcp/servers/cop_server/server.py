"""FastMCP server hosting the Cop agent."""

from cop_thief_mcp.servers.common import build_agent_server
from cop_thief_mcp.services.game.grid import Role
from cop_thief_mcp.shared.mcp_config import load_mcp_servers_config

mcp = build_agent_server(name="cop-server", role=Role.COP, ready_message="cop-server-ready")


def main() -> None:  # pragma: no cover - process entry point, exercised manually/in integration
    endpoint = load_mcp_servers_config().cop_server
    mcp.run(transport="http", host=endpoint.host, port=endpoint.port)


if __name__ == "__main__":  # pragma: no cover
    main()
