"""Run a full local game series and email the Internal Game JSON report at the end.

    uv run python -m cop_thief_mcp.cli.run_series

This is the "real" entry point matching the task doc's requirement that
the report be sent automatically once the 6-game series completes.
Requires GOOGLE_CLIENT_SECRET_PATH in .env (see .env-example); the report
goes to config/setup.json's `report_recipient`.
"""

from cop_thief_mcp.orchestrator.local_runner import run_full_local_series
from cop_thief_mcp.services.game.grid import Grid, Position
from cop_thief_mcp.shared.config import load_config


def main() -> None:  # pragma: no cover - thin CLI entry point, exercised manually
    config = load_config()
    grid = Grid(rows=config.grid_rows, cols=config.grid_cols)
    starts = [(Position(0, 0), Position(grid.rows - 1, grid.cols - 1)) for _ in range(config.num_games)]

    result = run_full_local_series(starts, send_report=True)

    print(f"Final totals -- cop: {result.cop_total}, thief: {result.thief_total}")
    print(f"Report sent to {config.report_recipient}")


if __name__ == "__main__":  # pragma: no cover
    main()
