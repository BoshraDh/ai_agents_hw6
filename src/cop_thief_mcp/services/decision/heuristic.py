"""Stage 4 default decision policy: greedy chase (Cop) / greedy flee (Thief).

Thief: moves to maximize Manhattan distance from the Cop, tie-breaking
toward cells with more open escape neighbors so it doesn't greedily walk
itself into a corner.

Cop: a *pure* greedy minimize-distance-to-the-thief's-last-known-position
chase is vulnerable to a well-known pursuit-evasion pathology -- since the
Thief always reacts to the Cop's position *after* the Cop already committed
to its move, a purely reactive Cop can fall into a stable oscillation and
never close the gap, even from short range. To break this, the Cop looks
one ply ahead: for each candidate move, it simulates the Thief's best flee
response and picks the move that minimizes the *post-flee* distance,
instead of the distance to the Thief's stale current position.

Note: an earlier version of this heuristic also had the Cop spend a
barrier whenever it stood in a cell with few open neighbors. That measure
is *always* low in board corners/edges regardless of barriers (barriers
never block the Cop -- see rules.py), so it fired immediately at the
Cop's starting corner and wasted early turns barricading itself instead
of chasing. It was removed rather than patched further here; barrier
strategy is left to the optional Q-learning policy (q_learning.py), which
learns the value of PLACE_BARRIER from actual reward feedback instead of
a hand-coded rule.
"""

from cop_thief_mcp.services.game.grid import MOVE_ACTIONS, Action, Grid, Position, Role
from cop_thief_mcp.services.game.rules import is_move_legal


def manhattan_distance(a: Position, b: Position) -> int:
    return abs(a.row - b.row) + abs(a.col - b.col)


def _legal_moves(grid: Grid, position: Position, role: Role, barriers: frozenset[Position]) -> list[Action]:
    return [a for a in MOVE_ACTIONS if is_move_legal(grid, position, a, role, barriers)]


def _open_neighbor_count(grid: Grid, position: Position, role: Role, barriers: frozenset[Position]) -> int:
    return len(_legal_moves(grid, position, role, barriers))


def choose_thief_action(
    grid: Grid,
    position: Position,
    opponent_position: Position,
    barriers: frozenset[Position],
) -> Action:
    legal = _legal_moves(grid, position, Role.THIEF, barriers)
    if not legal:
        return Action.PASS

    def flee_score(action: Action) -> tuple[int, int]:
        candidate = position.moved(action)
        distance = manhattan_distance(candidate, opponent_position)
        mobility = _open_neighbor_count(grid, candidate, Role.THIEF, barriers)
        return (distance, mobility)

    return max(legal, key=flee_score)


def _post_flee_distance(
    grid: Grid, cop_candidate: Position, thief_position: Position, barriers: frozenset[Position]
) -> int:
    """Distance from `cop_candidate` to where the Thief will flee *in response* to it."""
    thief_reply = choose_thief_action(grid, thief_position, cop_candidate, barriers)
    thief_next = thief_position.moved(thief_reply) if thief_reply in MOVE_ACTIONS else thief_position
    return manhattan_distance(cop_candidate, thief_next)


def choose_cop_action(
    grid: Grid,
    position: Position,
    opponent_position: Position,
    barriers: frozenset[Position],
    barriers_placed: int,
    max_barriers: int,
) -> Action:
    legal = _legal_moves(grid, position, Role.COP, barriers)
    if not legal:
        return Action.PASS
    return min(legal, key=lambda a: _post_flee_distance(grid, position.moved(a), opponent_position, barriers))
