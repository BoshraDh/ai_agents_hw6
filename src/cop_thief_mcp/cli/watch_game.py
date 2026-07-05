"""Run a full local game series and print the ASCII grid after every turn.

    uv run python -m cop_thief_mcp.cli.watch_game

Uses whichever `decision_policy` is configured in config/setup.json.
Starting positions default to opposite corners for every sub-game; this is
a simple demo placement, not a strategy recommendation (see docs/PLAN.md).
"""

from cop_thief_mcp.orchestrator.local_runner import run_full_local_series
from cop_thief_mcp.services.game.grid import Grid, Position
from cop_thief_mcp.services.game.sub_game import OnTurn, TurnEvent
from cop_thief_mcp.services.visualization.grid_renderer import render_grid
from cop_thief_mcp.shared.config import load_config


def build_console_printer(grid: Grid) -> OnTurn:
    """Return an `on_turn` callback that prints the grid after each half-turn."""

    def _on_turn(event: TurnEvent) -> None:
        print(f"--- move {event.move_number + 1}: {event.role.value} played {event.action.value} ---")
        print(render_grid(grid, event.cop_position, event.thief_position, event.barriers))
        if event.captured:
            print(">>> CAPTURED <<<")
        print()

    return _on_turn


def main() -> None:  # pragma: no cover - thin CLI entry point, exercised manually
    config = load_config()
    grid = Grid(rows=config.grid_rows, cols=config.grid_cols)
    starts = [(Position(0, 0), Position(grid.rows - 1, grid.cols - 1)) for _ in range(config.num_games)]

    result = run_full_local_series(starts, on_turn=build_console_printer(grid))

    print(f"Final totals -- cop: {result.cop_total}, thief: {result.thief_total}")


if __name__ == "__main__":  # pragma: no cover
    main()
