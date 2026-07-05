from cop_thief_mcp.cli.watch_game import build_console_printer
from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role
from cop_thief_mcp.services.game.sub_game import TurnEvent


def test_prints_grid_and_move_header(capsys):
    grid = Grid(rows=2, cols=2)
    on_turn = build_console_printer(grid)

    on_turn(TurnEvent(0, Role.THIEF, Action.RIGHT, Position(0, 0), Position(0, 1), frozenset(), False))

    out = capsys.readouterr().out
    assert "move 1: thief played right" in out
    assert "C T" in out
    assert "CAPTURED" not in out


def test_prints_captured_marker_when_caught(capsys):
    grid = Grid(rows=2, cols=2)
    on_turn = build_console_printer(grid)

    on_turn(TurnEvent(4, Role.COP, Action.DOWN, Position(1, 1), Position(1, 1), frozenset(), True))

    out = capsys.readouterr().out
    assert "move 5: cop played down" in out
    assert "CAPTURED" in out
