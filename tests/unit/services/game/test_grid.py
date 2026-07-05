from cop_thief_mcp.services.game.grid import Action, Grid, Position


def test_position_moved_up():
    assert Position(2, 2).moved(Action.UP) == Position(1, 2)


def test_position_moved_down():
    assert Position(2, 2).moved(Action.DOWN) == Position(3, 2)


def test_position_moved_left():
    assert Position(2, 2).moved(Action.LEFT) == Position(2, 1)


def test_position_moved_right():
    assert Position(2, 2).moved(Action.RIGHT) == Position(2, 3)


def test_position_moved_pass_stays_put():
    assert Position(2, 2).moved(Action.PASS) == Position(2, 2)


def test_position_moved_place_barrier_stays_put():
    assert Position(2, 2).moved(Action.PLACE_BARRIER) == Position(2, 2)


def test_in_bounds_true_for_interior_cell():
    grid = Grid(rows=5, cols=5)
    assert grid.in_bounds(Position(2, 2)) is True


def test_in_bounds_false_for_negative_row():
    grid = Grid(rows=5, cols=5)
    assert grid.in_bounds(Position(-1, 0)) is False


def test_in_bounds_false_for_row_at_edge():
    grid = Grid(rows=5, cols=5)
    assert grid.in_bounds(Position(5, 0)) is False


def test_in_bounds_false_for_negative_col():
    grid = Grid(rows=5, cols=5)
    assert grid.in_bounds(Position(0, -1)) is False


def test_in_bounds_false_for_col_at_edge():
    grid = Grid(rows=5, cols=5)
    assert grid.in_bounds(Position(0, 5)) is False
