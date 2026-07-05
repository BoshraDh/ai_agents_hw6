from cop_thief_mcp.services.game.grid import Grid, Position
from cop_thief_mcp.services.visualization.grid_renderer import render_grid


def test_renders_empty_cells_and_actors_in_a_small_grid():
    grid = Grid(rows=2, cols=2)

    rendered = render_grid(grid, Position(0, 0), Position(1, 1), frozenset())

    assert rendered == "C .\n. T"


def test_renders_barriers():
    grid = Grid(rows=2, cols=2)

    rendered = render_grid(grid, Position(0, 0), Position(1, 1), frozenset({Position(0, 1)}))

    assert rendered == "C #\n. T"


def test_renders_capture_as_a_single_combined_marker():
    grid = Grid(rows=2, cols=2)

    rendered = render_grid(grid, Position(0, 0), Position(0, 0), frozenset())

    assert rendered == "X .\n. ."


def test_output_has_one_row_per_grid_row():
    grid = Grid(rows=3, cols=4)

    rendered = render_grid(grid, Position(0, 0), Position(2, 3), frozenset())

    assert len(rendered.split("\n")) == 3
    assert all(len(row.split(" ")) == 4 for row in rendered.split("\n"))
