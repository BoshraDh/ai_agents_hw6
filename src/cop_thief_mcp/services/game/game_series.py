"""Runs the full 6-sub-game series and accumulates scores."""

from dataclasses import dataclass

from cop_thief_mcp.services.game.grid import Grid, Position
from cop_thief_mcp.services.game.scoring import score_sub_game
from cop_thief_mcp.services.game.sub_game import Policy, SubGameResult, run_sub_game
from cop_thief_mcp.shared.config import GameConfig


@dataclass(frozen=True)
class GameSeriesResult:
    sub_games: tuple[SubGameResult, ...]
    cop_total: int
    thief_total: int


def run_game_series(
    grid: Grid,
    starts: list[tuple[Position, Position]],
    cop_policy: Policy,
    thief_policy: Policy,
    config: GameConfig,
) -> GameSeriesResult:
    """Play `config.num_games` sub-games back-to-back, accumulating cop/thief totals.

    `starts` supplies the (cop, thief) starting positions for each sub-game and
    must contain exactly `config.num_games` entries — placement strategy is a
    decision left to the caller (random draw, fixed layout, or later strategy).
    """
    if len(starts) != config.num_games:
        raise ValueError(f"expected {config.num_games} starting position pairs, got {len(starts)}")

    sub_games: list[SubGameResult] = []
    cop_total = 0
    thief_total = 0

    for cop_start, thief_start in starts:
        result = run_sub_game(
            grid, cop_start, thief_start, cop_policy, thief_policy,
            config.max_moves, config.max_barriers,
        )
        cop_score, thief_score = score_sub_game(result.outcome, config.scoring)
        cop_total += cop_score
        thief_total += thief_score
        sub_games.append(result)

    return GameSeriesResult(tuple(sub_games), cop_total, thief_total)
