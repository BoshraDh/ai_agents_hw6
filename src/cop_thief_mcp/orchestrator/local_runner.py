"""Runs a full Cop-vs-Thief game series through the two real, independent MCP servers.

This is Stage 3's deliverable: wiring, not intelligence. Both sides are
driven by Stage 3's placeholder random-legal-move policy (see
`services/decision/random_walk.py`); Stage 4 swaps in a real decision
policy behind the same `decide_move` tool without changing anything here.
"""

from cop_thief_mcp.orchestrator.mcp_policy import build_mcp_policy
from cop_thief_mcp.servers.cop_server.server import mcp as cop_mcp
from cop_thief_mcp.servers.lifecycle import start_http_server, stop_server
from cop_thief_mcp.servers.thief_server.server import mcp as thief_mcp
from cop_thief_mcp.services.game.game_series import GameSeriesResult, run_game_series
from cop_thief_mcp.services.game.grid import Grid, Position
from cop_thief_mcp.shared.async_bridge import AsyncBridge
from cop_thief_mcp.shared.config import GameConfig, load_config
from cop_thief_mcp.shared.mcp_config import McpServersConfig, load_mcp_servers_config


def _server_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/mcp"


def run_full_local_series(
    starts: list[tuple[Position, Position]],
    game_config: GameConfig | None = None,
    servers_config: McpServersConfig | None = None,
) -> GameSeriesResult:
    """Start both MCP servers locally, play a full series through them, then tear down."""
    game_config = game_config or load_config()
    servers_config = servers_config or load_mcp_servers_config()
    grid = Grid(rows=game_config.grid_rows, cols=game_config.grid_cols)

    bridge = AsyncBridge()
    try:
        cop_task = bridge.run(
            start_http_server(cop_mcp, servers_config.cop_server.host, servers_config.cop_server.port)
        )
        thief_task = bridge.run(
            start_http_server(
                thief_mcp, servers_config.thief_server.host, servers_config.thief_server.port
            )
        )
        try:
            cop_policy = build_mcp_policy(
                _server_url(servers_config.cop_server.host, servers_config.cop_server.port), bridge
            )
            thief_policy = build_mcp_policy(
                _server_url(servers_config.thief_server.host, servers_config.thief_server.port), bridge
            )
            return run_game_series(grid, starts, cop_policy, thief_policy, game_config)
        finally:
            bridge.run(stop_server(cop_task))
            bridge.run(stop_server(thief_task))
    finally:
        bridge.close()
