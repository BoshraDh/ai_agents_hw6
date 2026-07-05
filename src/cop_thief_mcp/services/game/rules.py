"""Movement legality, barrier placement, and win-condition checks."""

from cop_thief_mcp.services.game.grid import MOVE_ACTIONS, Action, Grid, Position, Role


def is_move_legal(
    grid: Grid,
    position: Position,
    action: Action,
    role: Role,
    barriers: frozenset[Position],
) -> bool:
    """A move is legal if it lands in bounds and, for the Thief only, avoids barriers."""
    if action not in MOVE_ACTIONS:
        return False
    target = position.moved(action)
    if not grid.in_bounds(target):
        return False
    return not (role is Role.THIEF and target in barriers)


def can_place_barrier(role: Role, barriers_placed: int, max_barriers: int) -> bool:
    """Only the Cop may place barriers, up to the configured per-sub-game maximum."""
    return role is Role.COP and barriers_placed < max_barriers


def is_capture(cop_position: Position, thief_position: Position) -> bool:
    """The Cop wins by landing exactly on the Thief's cell."""
    return cop_position == thief_position


def thief_survives(moves_made: int, max_moves: int) -> bool:
    """The Thief wins by surviving the full sub-game without being caught."""
    return moves_made >= max_moves
