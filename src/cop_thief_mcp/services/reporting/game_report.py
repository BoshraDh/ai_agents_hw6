"""Builds the Internal Game JSON report (task doc section 9.1) from a
completed GameSeriesResult. Pure function, no I/O.
"""

from cop_thief_mcp.services.game.game_series import GameSeriesResult
from cop_thief_mcp.services.game.scoring import score_sub_game
from cop_thief_mcp.shared.config import GameConfig
from cop_thief_mcp.shared.mcp_config import McpServersConfig


def _server_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/mcp"


def build_game_report(
    result: GameSeriesResult, game_config: GameConfig, servers_config: McpServersConfig
) -> dict:
    """Build the Internal Game JSON report for one completed 6-sub-game series."""
    sub_games = []
    for sub_game in result.sub_games:
        cop_score, thief_score = score_sub_game(sub_game.outcome, game_config.scoring)
        sub_games.append(
            {
                "outcome": sub_game.outcome.value,
                "moves": sub_game.moves_made,
                "cop_score": cop_score,
                "thief_score": thief_score,
            }
        )

    return {
        "group_name": game_config.group_name,
        "students": [],
        "github_repo": game_config.github_repo,
        "cop_mcp_url": _server_url(servers_config.cop_server.host, servers_config.cop_server.port),
        "thief_mcp_url": _server_url(servers_config.thief_server.host, servers_config.thief_server.port),
        "timezone": "Asia/Jerusalem",
        "sub_games": sub_games,
        "totals": {"cop": result.cop_total, "thief": result.thief_total},
    }
