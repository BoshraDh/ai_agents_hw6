from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role
from cop_thief_mcp.services.game.rules import (
    can_place_barrier,
    is_capture,
    is_move_legal,
    thief_survives,
)

GRID = Grid(rows=5, cols=5)


def test_move_legal_within_bounds_no_barriers():
    assert is_move_legal(GRID, Position(2, 2), Action.UP, Role.COP, frozenset()) is True


def test_move_illegal_out_of_bounds():
    assert is_move_legal(GRID, Position(0, 0), Action.UP, Role.COP, frozenset()) is False


def test_move_illegal_action_is_not_a_movement():
    assert is_move_legal(GRID, Position(2, 2), Action.PLACE_BARRIER, Role.COP, frozenset()) is False


def test_thief_blocked_by_barrier():
    barriers = frozenset({Position(1, 2)})
    assert is_move_legal(GRID, Position(2, 2), Action.UP, Role.THIEF, barriers) is False


def test_cop_not_blocked_by_barrier():
    barriers = frozenset({Position(1, 2)})
    assert is_move_legal(GRID, Position(2, 2), Action.UP, Role.COP, barriers) is True


def test_cop_can_place_barrier_under_limit():
    assert can_place_barrier(Role.COP, barriers_placed=2, max_barriers=5) is True


def test_cop_cannot_place_barrier_at_limit():
    assert can_place_barrier(Role.COP, barriers_placed=5, max_barriers=5) is False


def test_thief_cannot_place_barrier():
    assert can_place_barrier(Role.THIEF, barriers_placed=0, max_barriers=5) is False


def test_is_capture_true_when_same_cell():
    assert is_capture(Position(1, 1), Position(1, 1)) is True


def test_is_capture_false_when_different_cell():
    assert is_capture(Position(1, 1), Position(1, 2)) is False


def test_thief_survives_true_at_max_moves():
    assert thief_survives(moves_made=25, max_moves=25) is True


def test_thief_survives_false_before_max_moves():
    assert thief_survives(moves_made=24, max_moves=25) is False
