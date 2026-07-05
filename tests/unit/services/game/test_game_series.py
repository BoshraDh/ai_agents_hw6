import pytest

from cop_thief_mcp.services.game.game_series import run_game_series
from cop_thief_mcp.services.game.grid import Action, Grid, Position
from cop_thief_mcp.services.game.scoring import SubGameOutcome
from cop_thief_mcp.shared.config import GameConfig, ScoringConfig

GRID = Grid(rows=5, cols=5)
SCORING = ScoringConfig(cop_win_cop=20, cop_win_thief=5, thief_win_cop=5, thief_win_thief=10)


def _config(num_games: int) -> GameConfig:
    return GameConfig(
        version="1.00",
        grid_rows=5,
        grid_cols=5,
        max_moves=25,
        num_games=num_games,
        max_barriers=5,
        decision_policy="heuristic",
        scoring=SCORING,
    )


def _cop_moves_right(_context):
    return Action.RIGHT


def _thief_always_passes(_context):
    return Action.PASS


def test_series_accumulates_totals_over_all_sub_games():
    config = _config(num_games=6)
    starts = [(Position(2, 0), Position(2, 1)) for _ in range(config.num_games)]

    result = run_game_series(GRID, starts, _cop_moves_right, _thief_always_passes, config)

    assert len(result.sub_games) == 6
    assert all(sg.outcome is SubGameOutcome.COP_WINS for sg in result.sub_games)
    assert result.cop_total == 6 * 20
    assert result.thief_total == 6 * 5


def test_series_rejects_wrong_number_of_start_positions():
    config = _config(num_games=6)
    starts = [(Position(0, 0), Position(0, 1))]

    with pytest.raises(ValueError):
        run_game_series(GRID, starts, _cop_moves_right, _thief_always_passes, config)
