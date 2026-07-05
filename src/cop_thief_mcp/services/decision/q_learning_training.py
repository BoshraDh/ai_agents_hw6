"""Self-play training loop for the Q-learning policy (see q_learning.py).

A self-contained episode simulator built on the same low-level primitives
as Stage 1's engine (Grid, is_move_legal, is_capture, can_place_barrier) —
but distinct from `run_sub_game`, since training needs per-step reward
signals that the real game runner has no reason to expose.
"""

import random

from cop_thief_mcp.services.decision.q_learning import QTable, encode_state, legal_actions
from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role
from cop_thief_mcp.services.game.rules import can_place_barrier, is_capture, is_move_legal

_CAPTURE_REWARD = 100.0
_CAUGHT_PENALTY = -100.0
_COP_STEP_PENALTY = -1.0
_THIEF_SURVIVAL_REWARD = 1.0


def _pick_action(table: QTable, state, choices: list[Action], epsilon: float, rng: random.Random) -> Action:
    if not choices:
        return Action.PASS
    if rng.random() < epsilon:
        return rng.choice(choices)
    return table.best_action(state, choices)


def _apply_action(
    grid: Grid,
    position: Position,
    action: Action,
    role: Role,
    barriers: set[Position],
    barriers_placed: int,
    max_barriers: int,
) -> tuple[Position, int]:
    if action is Action.PLACE_BARRIER:
        if can_place_barrier(role, barriers_placed, max_barriers):
            barriers.add(position)
            return position, barriers_placed + 1
        return position, barriers_placed
    if is_move_legal(grid, position, action, role, frozenset(barriers)):
        return position.moved(action), barriers_placed
    return position, barriers_placed


def _cop_choices(grid: Grid, position: Position, barriers: set[Position], barriers_placed: int, max_barriers: int):
    moves = legal_actions(grid, position, Role.COP, frozenset(barriers))
    if barriers_placed < max_barriers:
        return [*moves, Action.PLACE_BARRIER]
    return moves


def run_training_episode(
    grid: Grid,
    max_moves: int,
    max_barriers: int,
    cop_table: QTable,
    thief_table: QTable,
    alpha: float,
    gamma: float,
    epsilon: float,
    rng: random.Random,
    cop_start: Position,
    thief_start: Position,
) -> None:
    """Play one self-play sub-game, updating both tables via the Bellman equation."""
    cop_pos = cop_start
    thief_pos = thief_start
    barriers: set[Position] = set()
    barriers_placed = 0

    for _ in range(max_moves):
        thief_state = encode_state(thief_pos, cop_pos)
        thief_choices = legal_actions(grid, thief_pos, Role.THIEF, frozenset(barriers))
        thief_action = _pick_action(thief_table, thief_state, thief_choices, epsilon, rng)
        new_thief_pos, barriers_placed = _apply_action(
            grid, thief_pos, thief_action, Role.THIEF, barriers, barriers_placed, max_barriers
        )
        caught = is_capture(cop_pos, new_thief_pos)
        thief_table.update(
            thief_state, thief_action, _CAUGHT_PENALTY if caught else _THIEF_SURVIVAL_REWARD,
            encode_state(new_thief_pos, cop_pos),
            legal_actions(grid, new_thief_pos, Role.THIEF, frozenset(barriers)), caught, alpha, gamma,
        )
        thief_pos = new_thief_pos
        if caught:
            return

        cop_state = encode_state(cop_pos, thief_pos)
        cop_choices = _cop_choices(grid, cop_pos, barriers, barriers_placed, max_barriers)
        cop_action = _pick_action(cop_table, cop_state, cop_choices, epsilon, rng)
        new_cop_pos, barriers_placed = _apply_action(
            grid, cop_pos, cop_action, Role.COP, barriers, barriers_placed, max_barriers
        )
        captured = is_capture(new_cop_pos, thief_pos)
        cop_table.update(
            cop_state, cop_action, _CAPTURE_REWARD if captured else _COP_STEP_PENALTY,
            encode_state(new_cop_pos, thief_pos),
            _cop_choices(grid, new_cop_pos, barriers, barriers_placed, max_barriers), captured, alpha, gamma,
        )
        cop_pos = new_cop_pos
        if captured:
            return


def _random_position(grid: Grid, rng: random.Random) -> Position:
    return Position(rng.randrange(grid.rows), rng.randrange(grid.cols))


def train_q_tables(
    grid: Grid,
    max_moves: int,
    max_barriers: int,
    episodes: int = 2000,
    alpha: float = 0.1,
    gamma: float = 0.9,
    epsilon: float = 0.15,
    seed: int = 42,
) -> tuple[QTable, QTable]:
    """Train Cop/Thief Q-tables via simultaneous self-play over `episodes` sub-games.

    Starting positions are randomized every episode (rather than fixed, e.g.
    at opposite corners) so the tables see -- and learn good actions for --
    close-range and edge-case relative states too, not just the ones
    reachable from one specific starting layout.
    """
    rng = random.Random(seed)
    cop_table, thief_table = QTable(), QTable()
    for _ in range(episodes):
        cop_start = _random_position(grid, rng)
        thief_start = _random_position(grid, rng)
        run_training_episode(
            grid, max_moves, max_barriers, cop_table, thief_table, alpha, gamma, epsilon, rng, cop_start, thief_start
        )
    return cop_table, thief_table
