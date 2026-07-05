"""Stage 3 placeholder decision: a uniformly random legal movement action.

Exists only to prove the MCP request/response wiring end-to-end; a real
heuristic or Q-table policy replaces this behind the same `decide_move`
tool interface in Stage 4.
"""

import random

from cop_thief_mcp.services.game.grid import MOVE_ACTIONS, Action, Grid, Position, Role
from cop_thief_mcp.services.game.rules import is_move_legal


def choose_random_legal_action(
    grid: Grid,
    position: Position,
    role: Role,
    barriers: frozenset[Position],
) -> Action:
    """Pick uniformly among legal movement actions, or PASS if none are available."""
    legal = [a for a in MOVE_ACTIONS if is_move_legal(grid, position, a, role, barriers)]
    return random.choice(legal) if legal else Action.PASS
