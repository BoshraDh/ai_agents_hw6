"""Runs a single sub-game: Thief-first alternating turns, capped at max_moves.

Decision-making is injected as a `Policy` callable so this engine stays pure
and agnostic to how a move is chosen (scripted, heuristic, Q-table, or LLM/MCP
in later stages).
"""

from collections.abc import Callable
from dataclasses import dataclass

from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role
from cop_thief_mcp.services.game.rules import can_place_barrier, is_capture, is_move_legal
from cop_thief_mcp.services.game.scoring import SubGameOutcome


@dataclass(frozen=True)
class TurnContext:
    """Full state handed to a policy function for the side whose turn it is."""

    role: Role
    own_position: Position
    opponent_position: Position
    grid: Grid
    barriers: frozenset[Position]
    moves_made: int
    max_moves: int
    barriers_placed: int
    max_barriers: int


Policy = Callable[[TurnContext], Action]


@dataclass(frozen=True)
class TurnEvent:
    """Reported to an optional `on_turn` callback after each half-turn, for
    observers (e.g. a CLI/GUI visualizer) that want to watch the game unfold
    without the engine itself knowing anything about rendering.
    """

    move_number: int
    role: Role
    action: Action
    cop_position: Position
    thief_position: Position
    barriers: frozenset[Position]
    captured: bool


OnTurn = Callable[[TurnEvent], None]


@dataclass(frozen=True)
class SubGameResult:
    outcome: SubGameOutcome
    moves_made: int
    cop_position: Position
    thief_position: Position
    barriers: frozenset[Position]


def _resolve_turn(
    role: Role,
    own_pos: Position,
    opponent_pos: Position,
    grid: Grid,
    barriers: set[Position],
    policy: Policy,
    moves_made: int,
    max_moves: int,
    barriers_placed: int,
    max_barriers: int,
) -> tuple[Position, int, Action]:
    """Ask the policy for an action and apply it, returning (new_position, new_barriers_placed, action)."""
    context = TurnContext(
        role=role,
        own_position=own_pos,
        opponent_position=opponent_pos,
        grid=grid,
        barriers=frozenset(barriers),
        moves_made=moves_made,
        max_moves=max_moves,
        barriers_placed=barriers_placed,
        max_barriers=max_barriers,
    )
    action = policy(context)

    if action is Action.PLACE_BARRIER and can_place_barrier(role, barriers_placed, max_barriers):
        barriers.add(own_pos)
        return own_pos, barriers_placed + 1, action

    if is_move_legal(grid, own_pos, action, role, frozenset(barriers)):
        return own_pos.moved(action), barriers_placed, action

    return own_pos, barriers_placed, action


def run_sub_game(
    grid: Grid,
    cop_start: Position,
    thief_start: Position,
    cop_policy: Policy,
    thief_policy: Policy,
    max_moves: int,
    max_barriers: int,
    on_turn: OnTurn | None = None,
) -> SubGameResult:
    """Play one sub-game: Thief moves, then Cop, alternating, until capture or max_moves.

    `on_turn`, if given, is called after every individual move (Thief's, then
    Cop's) with a `TurnEvent` -- purely for observation (e.g. visualization);
    it cannot affect the outcome.
    """
    cop_pos, thief_pos = cop_start, thief_start
    barriers: set[Position] = set()
    barriers_placed = 0

    for move_number in range(max_moves):
        thief_pos, _, thief_action = _resolve_turn(
            Role.THIEF, thief_pos, cop_pos, grid, barriers, thief_policy,
            move_number, max_moves, barriers_placed, max_barriers,
        )
        captured = is_capture(cop_pos, thief_pos)
        if on_turn:
            on_turn(TurnEvent(move_number, Role.THIEF, thief_action, cop_pos, thief_pos, frozenset(barriers), captured))
        if captured:
            return SubGameResult(
                SubGameOutcome.COP_WINS, move_number + 1, cop_pos, thief_pos, frozenset(barriers)
            )

        cop_pos, barriers_placed, cop_action = _resolve_turn(
            Role.COP, cop_pos, thief_pos, grid, barriers, cop_policy,
            move_number, max_moves, barriers_placed, max_barriers,
        )
        captured = is_capture(cop_pos, thief_pos)
        if on_turn:
            on_turn(TurnEvent(move_number, Role.COP, cop_action, cop_pos, thief_pos, frozenset(barriers), captured))
        if captured:
            return SubGameResult(
                SubGameOutcome.COP_WINS, move_number + 1, cop_pos, thief_pos, frozenset(barriers)
            )

    return SubGameResult(SubGameOutcome.THIEF_WINS, max_moves, cop_pos, thief_pos, frozenset(barriers))
