"""Proves run_full_local_series triggers the end-of-series report exactly
when send_report=True. The report-sending itself is mocked -- this test
never sends a real email.
"""

from unittest.mock import patch

from cop_thief_mcp.orchestrator.local_runner import run_full_local_series
from cop_thief_mcp.services.game.grid import Position
from cop_thief_mcp.shared.config import GameConfig, ScoringConfig
from cop_thief_mcp.shared.mcp_config import McpServersConfig, ServerEndpoint

HOST = "127.0.0.1"

TEST_GAME_CONFIG = GameConfig(
    version="1.00", grid_rows=3, grid_cols=3, max_moves=5, num_games=1, max_barriers=2,
    decision_policy="heuristic", report_recipient="rmisegal+uoh26b@gmail.com",
    github_repo="https://github.com/BoshraDh/ai_agents_hw6.git", group_name="BoshraDh",
    scoring=ScoringConfig(cop_win_cop=20, cop_win_thief=5, thief_win_cop=5, thief_win_thief=10),
)


def _servers_config(cop_port: int, thief_port: int) -> McpServersConfig:
    return McpServersConfig(
        version="1.00",
        cop_server=ServerEndpoint(host=HOST, port=cop_port),
        thief_server=ServerEndpoint(host=HOST, port=thief_port),
    )


def test_send_report_true_triggers_the_report_flow():
    starts = [(Position(0, 0), Position(2, 2))]

    with patch("cop_thief_mcp.orchestrator.local_runner.send_series_report") as mock_send:
        servers_config = _servers_config(8199, 8200)
        result = run_full_local_series(starts, TEST_GAME_CONFIG, servers_config, send_report=True)

    mock_send.assert_called_once_with(result, TEST_GAME_CONFIG, servers_config)


def test_send_report_defaults_to_false_and_never_sends():
    starts = [(Position(0, 0), Position(2, 2))]

    with patch("cop_thief_mcp.orchestrator.local_runner.send_series_report") as mock_send:
        servers_config = _servers_config(8201, 8202)
        run_full_local_series(starts, TEST_GAME_CONFIG, servers_config)

    mock_send.assert_not_called()
