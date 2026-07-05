from cop_thief_mcp.services.game.game_series import GameSeriesResult
from cop_thief_mcp.services.game.grid import Position
from cop_thief_mcp.services.game.scoring import SubGameOutcome
from cop_thief_mcp.services.game.sub_game import SubGameResult
from cop_thief_mcp.services.reporting.game_report import build_game_report
from cop_thief_mcp.shared.config import GameConfig, ScoringConfig
from cop_thief_mcp.shared.mcp_config import McpServersConfig, ServerEndpoint

SCORING = ScoringConfig(cop_win_cop=20, cop_win_thief=5, thief_win_cop=5, thief_win_thief=10)

GAME_CONFIG = GameConfig(
    version="1.00", grid_rows=5, grid_cols=5, max_moves=25, num_games=2, max_barriers=5,
    decision_policy="heuristic", report_recipient="rmisegal+uoh26b@gmail.com",
    github_repo="https://github.com/BoshraDh/ai_agents_hw6.git", group_name="BoshraDh",
    scoring=SCORING,
)

SERVERS_CONFIG = McpServersConfig(
    version="1.00",
    cop_server=ServerEndpoint(host="127.0.0.1", port=8001),
    thief_server=ServerEndpoint(host="127.0.0.1", port=8002),
)


def test_build_game_report_has_the_expected_shape():
    result = GameSeriesResult(
        sub_games=(
            SubGameResult(SubGameOutcome.COP_WINS, 5, Position(1, 1), Position(1, 1), frozenset()),
            SubGameResult(SubGameOutcome.THIEF_WINS, 25, Position(0, 0), Position(4, 4), frozenset()),
        ),
        cop_total=25,
        thief_total=15,
    )

    report = build_game_report(result, GAME_CONFIG, SERVERS_CONFIG)

    assert report == {
        "group_name": "BoshraDh",
        "students": [],
        "github_repo": "https://github.com/BoshraDh/ai_agents_hw6.git",
        "cop_mcp_url": "http://127.0.0.1:8001/mcp",
        "thief_mcp_url": "http://127.0.0.1:8002/mcp",
        "timezone": "Asia/Jerusalem",
        "sub_games": [
            {"outcome": "cop_wins", "moves": 5, "cop_score": 20, "thief_score": 5},
            {"outcome": "thief_wins", "moves": 25, "cop_score": 5, "thief_score": 10},
        ],
        "totals": {"cop": 25, "thief": 15},
    }
