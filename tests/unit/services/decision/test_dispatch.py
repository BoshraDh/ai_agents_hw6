from cop_thief_mcp.services.decision.dispatch import choose_action
from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role

GRID = Grid(rows=5, cols=5)


def test_heuristic_is_the_default_policy_for_cop():
    action = choose_action(
        "heuristic", Role.COP, GRID, Position(2, 2), Position(2, 4), frozenset(), 0, 5
    )

    assert action is Action.RIGHT


def test_heuristic_is_the_default_policy_for_thief():
    action = choose_action(
        "heuristic", Role.THIEF, GRID, Position(2, 2), Position(2, 0), frozenset(), 0, 5
    )

    assert action is Action.UP


def test_random_walk_policy_returns_a_legal_action():
    action = choose_action(
        "random_walk", Role.THIEF, GRID, Position(0, 0), Position(4, 4), frozenset(), 0, 5
    )

    assert action in {Action.DOWN, Action.RIGHT}


def test_unknown_policy_name_falls_back_to_heuristic():
    action = choose_action(
        "not-a-real-policy", Role.COP, GRID, Position(2, 2), Position(2, 4), frozenset(), 0, 5
    )

    assert action is Action.RIGHT


def test_q_learning_without_a_table_falls_back_to_heuristic():
    action = choose_action(
        "q_learning", Role.COP, GRID, Position(2, 2), Position(2, 4), frozenset(), 0, 5, q_table=None
    )

    assert action is Action.RIGHT
