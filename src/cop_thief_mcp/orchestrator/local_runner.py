"""Runs a full Cop-vs-Thief game series through the two real, independent MCP servers.

The policy-building strategy matches whichever `decision_policy` the two
already-built server objects were configured with at import time (see
`servers/cop_server/server.py` / `servers/thief_server/server.py`):
ground-truth position sharing for `heuristic`/`random_walk`/`q_learning`
(Stage 4), or free-text message exchange for `llm` (Stage 5).
"""

from cop_thief_mcp.orchestrator.mcp_policy import build_mcp_message_policy, build_mcp_policy
from cop_thief_mcp.orchestrator.message_exchange import MessageExchange
from cop_thief_mcp.servers.cop_server.server import mcp as cop_mcp
from cop_thief_mcp.servers.lifecycle import start_http_server, stop_server
from cop_thief_mcp.servers.thief_server.server import mcp as thief_mcp
from cop_thief_mcp.services.decision.dispatch import LLM
from cop_thief_mcp.services.game.game_series import GameSeriesResult, run_game_series
from cop_thief_mcp.services.game.grid import Grid, Position, Role
from cop_thief_mcp.services.game.sub_game import OnTurn
from cop_thief_mcp.shared.async_bridge import AsyncBridge
from cop_thief_mcp.shared.config import GameConfig, load_config
from cop_thief_mcp.shared.mcp_config import McpServersConfig, load_mcp_servers_config


def _server_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/mcp"


def _build_policies(game_config: GameConfig, cop_url: str, thief_url: str, bridge: AsyncBridge):
    if game_config.decision_policy == LLM:
        exchange = MessageExchange()
        return (
            build_mcp_message_policy(cop_url, bridge, exchange, Role.COP),
            build_mcp_message_policy(thief_url, bridge, exchange, Role.THIEF),
        )
    return build_mcp_policy(cop_url, bridge), build_mcp_policy(thief_url, bridge)


def run_full_local_series(
    starts: list[tuple[Position, Position]],
    game_config: GameConfig | None = None,
    servers_config: McpServersConfig | None = None,
    on_turn: OnTurn | None = None,
) -> GameSeriesResult:
    """Start both MCP servers locally, play a full series through them, then tear down.

    `on_turn`, if given, is forwarded to the engine for observation only
    (e.g. a CLI/GUI visualizer) — see `services/visualization/grid_renderer.py`.
    """
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
            cop_policy, thief_policy = _build_policies(
                game_config,
                _server_url(servers_config.cop_server.host, servers_config.cop_server.port),
                _server_url(servers_config.thief_server.host, servers_config.thief_server.port),
                bridge,
            )
            return run_game_series(grid, starts, cop_policy, thief_policy, game_config, on_turn)
        finally:
            bridge.run(stop_server(cop_task))
            bridge.run(stop_server(thief_task))
    finally:
        bridge.close()
