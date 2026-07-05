"""Loads all game parameters from config/setup.json. No hard-coded game values elsewhere."""

from dataclasses import dataclass
from pathlib import Path

from cop_thief_mcp.shared.constants import DEFAULT_CONFIG_PATH
from cop_thief_mcp.shared.json_loader import read_json


@dataclass(frozen=True)
class ScoringConfig:
    cop_win_cop: int
    cop_win_thief: int
    thief_win_cop: int
    thief_win_thief: int


@dataclass(frozen=True)
class GameConfig:
    version: str
    grid_rows: int
    grid_cols: int
    max_moves: int
    num_games: int
    max_barriers: int
    scoring: ScoringConfig


def load_config(path: Path | None = None) -> GameConfig:
    """Read and validate the game configuration from a JSON file."""
    config_path = path or DEFAULT_CONFIG_PATH
    raw = read_json(config_path)

    rows, cols = raw["grid_size"]
    scoring_raw = raw["scoring"]

    return GameConfig(
        version=raw["version"],
        grid_rows=rows,
        grid_cols=cols,
        max_moves=raw["max_moves"],
        num_games=raw["num_games"],
        max_barriers=raw["max_barriers"],
        scoring=ScoringConfig(
            cop_win_cop=scoring_raw["cop_win"]["cop"],
            cop_win_thief=scoring_raw["cop_win"]["thief"],
            thief_win_cop=scoring_raw["thief_win"]["cop"],
            thief_win_thief=scoring_raw["thief_win"]["thief"],
        ),
    )
