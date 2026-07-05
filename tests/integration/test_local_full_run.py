"""Proves Stage 3's deliverable: a full game series runs end-to-end through the real,
independent Cop/Thief MCP servers, driven entirely by real HTTP tool calls.
"""

from cop_thief_mcp.orchestrator.local_runner import run_full_local_series
from cop_thief_mcp.services.game.grid import Position
from cop_thief_mcp.shared.config import GameConfig, ScoringConfig
from cop_thief_mcp.shared.mcp_config import McpServersConfig, ServerEndpoint

HOST = "127.0.0.1"
COP_TEST_PORT = 8095
THIEF_TEST_PORT = 8096

TEST_GAME_CONFIG = GameConfig(
    version="1.00",
    grid_rows=3,
    grid_cols=3,
    max_moves=10,
    num_games=3,
    max_barriers=5,
    decision_policy="heuristic",
    report_recipient="test@example.com",
    github_repo="https://github.com/example/example.git",
    group_name="test-group",
    scoring=ScoringConfig(cop_win_cop=20, cop_win_thief=5, thief_win_cop=5, thief_win_thief=10),
)

TEST_SERVERS_CONFIG = McpServersConfig(
    version="1.00",
    cop_server=ServerEndpoint(host=HOST, port=COP_TEST_PORT),
    thief_server=ServerEndpoint(host=HOST, port=THIEF_TEST_PORT),
)


def test_full_local_series_runs_end_to_end_through_real_mcp_servers():
    starts = [(Position(0, 0), Position(2, 2)) for _ in range(TEST_GAME_CONFIG.num_games)]

    result = run_full_local_series(starts, TEST_GAME_CONFIG, TEST_SERVERS_CONFIG)

    assert len(result.sub_games) == TEST_GAME_CONFIG.num_games
    for sub_game in result.sub_games:
        assert 1 <= sub_game.moves_made <= TEST_GAME_CONFIG.max_moves
    assert result.cop_total >= 0
    assert result.thief_total >= 0
