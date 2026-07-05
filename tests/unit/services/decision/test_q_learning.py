from cop_thief_mcp.services.decision.q_learning import (
    QTable,
    choose_action,
    encode_state,
    legal_actions,
)
from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role


def test_encode_state_clamps_within_range():
    assert encode_state(Position(2, 2), Position(3, 2)) == (1, 0)


def test_encode_state_clamps_beyond_range():
    assert encode_state(Position(0, 0), Position(4, 4)) == (2, 2)
    assert encode_state(Position(4, 4), Position(0, 0)) == (-2, -2)


def test_qtable_get_defaults_to_zero():
    table = QTable()
    assert table.get((0, 0), Action.UP) == 0.0


def test_qtable_best_action_picks_highest_value():
    table = QTable()
    table.values[((0, 0), Action.UP)] = 1.0
    table.values[((0, 0), Action.DOWN)] = 5.0

    assert table.best_action((0, 0), [Action.UP, Action.DOWN]) is Action.DOWN


def test_qtable_best_action_with_no_choices_returns_pass():
    table = QTable()
    assert table.best_action((0, 0), []) is Action.PASS


def test_qtable_update_applies_bellman_equation():
    table = QTable()
    table.update(
        state=(0, 0),
        action=Action.UP,
        reward=10.0,
        next_state=(1, 0),
        next_choices=[Action.DOWN],
        done=False,
        alpha=0.5,
        gamma=0.9,
    )

    assert table.get((0, 0), Action.UP) == 5.0


def test_qtable_update_terminal_ignores_future_value():
    table = QTable()
    table.values[((1, 0), Action.DOWN)] = 100.0

    table.update(
        state=(0, 0),
        action=Action.UP,
        reward=10.0,
        next_state=(1, 0),
        next_choices=[Action.DOWN],
        done=True,
        alpha=0.5,
        gamma=0.9,
    )

    assert table.get((0, 0), Action.UP) == 5.0


def test_legal_actions_excludes_out_of_bounds_moves():
    grid = Grid(rows=5, cols=5)

    actions = legal_actions(grid, Position(0, 0), Role.COP, frozenset())

    assert Action.UP not in actions
    assert Action.LEFT not in actions


def test_choose_action_with_empty_table_picks_first_legal_move():
    table = QTable()
    grid = Grid(rows=5, cols=5)

    action = choose_action(table, grid, Position(2, 2), Position(4, 4), Role.THIEF, frozenset(), 0, 0)

    assert action is Action.UP  # first in MOVE_ACTIONS order, all tied at 0.0


def test_choose_action_includes_place_barrier_choice_for_cop_with_barriers_remaining():
    table = QTable()
    grid = Grid(rows=5, cols=5)
    state = encode_state(Position(2, 2), Position(2, 4))
    table.values[(state, Action.PLACE_BARRIER)] = 99.0

    action = choose_action(table, grid, Position(2, 2), Position(2, 4), Role.COP, frozenset(), 0, 5)

    assert action is Action.PLACE_BARRIER


def test_choose_action_excludes_place_barrier_when_none_remain():
    table = QTable()
    grid = Grid(rows=5, cols=5)
    state = encode_state(Position(2, 2), Position(2, 4))
    table.values[(state, Action.PLACE_BARRIER)] = 99.0

    action = choose_action(table, grid, Position(2, 2), Position(2, 4), Role.COP, frozenset(), 5, 5)

    assert action is not Action.PLACE_BARRIER
