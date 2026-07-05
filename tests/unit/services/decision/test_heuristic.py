from cop_thief_mcp.services.decision.heuristic import choose_cop_action, choose_thief_action
from cop_thief_mcp.services.game.grid import Action, Grid, Position


def test_cop_chases_greedily_in_open_space():
    grid = Grid(rows=5, cols=5)

    action = choose_cop_action(
        grid, Position(2, 2), Position(2, 4), frozenset(), barriers_placed=0, max_barriers=5
    )

    assert action is Action.RIGHT


def test_cop_captures_immediately_when_adjacent():
    grid = Grid(rows=5, cols=5)

    action = choose_cop_action(
        grid, Position(2, 2), Position(2, 3), frozenset(), barriers_placed=0, max_barriers=5
    )

    assert action is Action.RIGHT


def test_cop_does_not_get_stuck_barricading_its_own_starting_corner():
    # Regression test: a Cop starting in a board corner naturally has only 2
    # open neighbors, which an earlier (buggy) heuristic mistook for a
    # "narrow corridor" worth sealing instead of chasing.
    grid = Grid(rows=5, cols=5)

    action = choose_cop_action(
        grid, Position(0, 0), Position(1, 1), frozenset(), barriers_placed=0, max_barriers=5
    )

    assert action in {Action.DOWN, Action.RIGHT}


def test_cop_passes_when_no_legal_moves():
    grid = Grid(rows=1, cols=1)

    action = choose_cop_action(
        grid, Position(0, 0), Position(0, 0), frozenset(), barriers_placed=5, max_barriers=5
    )

    assert action is Action.PASS


def test_thief_flees_away_from_cop():
    grid = Grid(rows=5, cols=5)

    action = choose_thief_action(grid, Position(2, 2), Position(2, 0), frozenset())

    # UP, DOWN, and RIGHT all tie for max distance+mobility from an open
    # center cell; UP wins as the first-encountered tie per MOVE_ACTIONS order.
    assert action is Action.UP


def test_thief_breaks_distance_ties_toward_higher_mobility_cell():
    grid = Grid(rows=5, cols=5)

    action = choose_thief_action(grid, Position(1, 0), Position(1, 4), frozenset())

    assert action is Action.DOWN


def test_thief_passes_when_boxed_in_by_barriers():
    grid = Grid(rows=3, cols=3)
    barriers = frozenset({Position(0, 1), Position(1, 0), Position(1, 2), Position(2, 1)})

    action = choose_thief_action(grid, Position(1, 1), Position(0, 0), barriers)

    assert action is Action.PASS
