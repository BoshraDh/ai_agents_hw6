from cop_thief_mcp.services.decision.random_walk import choose_random_legal_action
from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role

GRID = Grid(rows=3, cols=3)


def test_returns_a_legal_action_in_open_space():
    action = choose_random_legal_action(GRID, Position(1, 1), Role.THIEF, frozenset())

    assert action in {Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT}


def test_passes_when_thief_is_boxed_in_by_barriers():
    barriers = frozenset({Position(0, 1), Position(1, 0), Position(1, 2), Position(2, 1)})

    action = choose_random_legal_action(GRID, Position(1, 1), Role.THIEF, barriers)

    assert action is Action.PASS


def test_cop_ignores_barriers_that_would_box_in_a_thief():
    barriers = frozenset({Position(0, 1), Position(1, 0), Position(1, 2), Position(2, 1)})

    action = choose_random_legal_action(GRID, Position(1, 1), Role.COP, barriers)

    assert action in {Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT}


def test_passes_when_in_a_corner_with_no_barriers_but_still_has_two_legal_moves():
    action = choose_random_legal_action(GRID, Position(0, 0), Role.THIEF, frozenset())

    assert action in {Action.DOWN, Action.RIGHT}
