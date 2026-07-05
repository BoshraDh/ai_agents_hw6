"""Selects and invokes the configured decision policy behind a single, uniform call site.

Keeps `servers/common.py` (the transport layer) free of decision logic,
per the SDK-layering rule: business logic lives in services/, not in the
FastMCP tool bodies themselves.
"""

from cop_thief_mcp.services.decision.heuristic import choose_cop_action, choose_thief_action
from cop_thief_mcp.services.decision.q_learning import QTable
from cop_thief_mcp.services.decision.q_learning import choose_action as choose_q_learning_action
from cop_thief_mcp.services.decision.random_walk import choose_random_legal_action
from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role

HEURISTIC = "heuristic"
RANDOM_WALK = "random_walk"
Q_LEARNING = "q_learning"


def choose_action(
    policy_name: str,
    role: Role,
    grid: Grid,
    position: Position,
    opponent_position: Position,
    barriers: frozenset[Position],
    barriers_placed: int,
    max_barriers: int,
    q_table: QTable | None = None,
) -> Action:
    """Dispatch to the named decision policy; falls back to the heuristic by default."""
    if policy_name == Q_LEARNING and q_table is not None:
        return choose_q_learning_action(
            q_table, grid, position, opponent_position, role, barriers, barriers_placed, max_barriers
        )
    if policy_name == RANDOM_WALK:
        return choose_random_legal_action(grid, position, role, barriers)
    if role is Role.COP:
        return choose_cop_action(grid, position, opponent_position, barriers, barriers_placed, max_barriers)
    return choose_thief_action(grid, position, opponent_position, barriers)
