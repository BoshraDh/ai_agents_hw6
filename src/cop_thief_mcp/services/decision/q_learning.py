"""Optional tabular Q-Learning decision policy (task doc section 8).

Bellman-equation updates over a small *relative-position* state space
(clamped opponent offset), so the table's size is independent of grid
size and stays fast to train. This is recommended enrichment, not the
default — `heuristic.py` is Stage 4's primary policy; Q-learning is
selectable behind the same `decide_move` tool via
`config/setup.json`'s `decision_policy` setting.
"""

from dataclasses import dataclass, field

from cop_thief_mcp.services.game.grid import MOVE_ACTIONS, Action, Grid, Position, Role
from cop_thief_mcp.services.game.rules import is_move_legal

State = tuple[int, int]

_REL_CLAMP = 2


def encode_state(own: Position, opponent: Position) -> State:
    """Clamp the opponent's relative offset so the state space stays small and
    generalizes across grid sizes, instead of scaling with absolute board size."""
    d_row = max(-_REL_CLAMP, min(_REL_CLAMP, opponent.row - own.row))
    d_col = max(-_REL_CLAMP, min(_REL_CLAMP, opponent.col - own.col))
    return (d_row, d_col)


def legal_actions(grid: Grid, position: Position, role: Role, barriers: frozenset[Position]) -> list[Action]:
    moves = [a for a in MOVE_ACTIONS if is_move_legal(grid, position, a, role, barriers)]
    return moves


@dataclass
class QTable:
    """Q(state, action) -> value, updated via the Bellman equation."""

    values: dict[tuple[State, Action], float] = field(default_factory=dict)

    def get(self, state: State, action: Action) -> float:
        return self.values.get((state, action), 0.0)

    def best_action(self, state: State, choices: list[Action]) -> Action:
        if not choices:
            return Action.PASS
        return max(choices, key=lambda a: self.get(state, a))

    def update(
        self,
        state: State,
        action: Action,
        reward: float,
        next_state: State,
        next_choices: list[Action],
        done: bool,
        alpha: float,
        gamma: float,
    ) -> None:
        best_next = 0.0 if done or not next_choices else max(self.get(next_state, a) for a in next_choices)
        td_target = reward + gamma * best_next
        td_error = td_target - self.get(state, action)
        self.values[(state, action)] = self.get(state, action) + alpha * td_error


def choose_action(
    table: QTable,
    grid: Grid,
    position: Position,
    opponent_position: Position,
    role: Role,
    barriers: frozenset[Position],
    barriers_placed: int,
    max_barriers: int,
) -> Action:
    """Greedy inference: the highest-value action for the current (clamped) state."""
    choices = legal_actions(grid, position, role, barriers)
    if role is Role.COP and barriers_placed < max_barriers:
        choices = [*choices, Action.PLACE_BARRIER]
    state = encode_state(position, opponent_position)
    return table.best_action(state, choices)
