"""Pure ASCII rendering of a board state, for CLI visualization only.

Never touched by the game engine -- this module only ever reads positions
and barriers to produce a display string; it has no influence on gameplay.
"""

from cop_thief_mcp.services.game.grid import Grid, Position

EMPTY = "."
COP = "C"
THIEF = "T"
BARRIER = "#"
CAPTURED = "X"


def render_grid(
    grid: Grid, cop_position: Position, thief_position: Position, barriers: frozenset[Position]
) -> str:
    """Render the board as a newline-separated ASCII grid, row 0 at the top."""
    rows = []
    for row in range(grid.rows):
        cells = [
            _render_cell(Position(row, col), cop_position, thief_position, barriers)
            for col in range(grid.cols)
        ]
        rows.append(" ".join(cells))
    return "\n".join(rows)


def _render_cell(
    position: Position, cop_position: Position, thief_position: Position, barriers: frozenset[Position]
) -> str:
    is_cop = position == cop_position
    is_thief = position == thief_position
    if is_cop and is_thief:
        return CAPTURED
    if is_cop:
        return COP
    if is_thief:
        return THIEF
    if position in barriers:
        return BARRIER
    return EMPTY
