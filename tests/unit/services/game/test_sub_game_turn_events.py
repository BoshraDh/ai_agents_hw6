from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role
from cop_thief_mcp.services.game.scoring import SubGameOutcome
from cop_thief_mcp.services.game.sub_game import TurnEvent, run_sub_game

GRID = Grid(rows=5, cols=5)


def _scripted(actions):
    queue = list(actions)

    def policy(_context):
        return queue.pop(0) if queue else Action.PASS

    return policy


def test_on_turn_is_not_required():
    # Existing callers that don't pass on_turn must keep working unchanged.
    result = run_sub_game(
        GRID, Position(0, 0), Position(0, 1),
        _scripted([Action.RIGHT]), _scripted([Action.PASS]),
        max_moves=25, max_barriers=5,
    )
    assert result.outcome is SubGameOutcome.COP_WINS


def test_on_turn_receives_one_event_per_half_turn():
    events: list[TurnEvent] = []

    run_sub_game(
        GRID, Position(0, 0), Position(4, 4),
        _scripted([]), _scripted([]),
        max_moves=3, max_barriers=5,
        on_turn=events.append,
    )

    # 3 full rounds * 2 half-turns (thief, then cop) each = 6 events
    assert len(events) == 6
    assert [e.role for e in events] == [
        Role.THIEF, Role.COP, Role.THIEF, Role.COP, Role.THIEF, Role.COP
    ]


def test_on_turn_reports_capture_and_stops_early():
    events: list[TurnEvent] = []

    result = run_sub_game(
        GRID, Position(0, 0), Position(0, 1),
        _scripted([Action.RIGHT]), _scripted([Action.PASS]),
        max_moves=25, max_barriers=5,
        on_turn=events.append,
    )

    assert result.outcome is SubGameOutcome.COP_WINS
    # Thief's PASS (no capture), then Cop's RIGHT (capture) -- exactly 2 events.
    assert len(events) == 2
    assert events[0].captured is False
    assert events[1].role is Role.COP
    assert events[1].captured is True
    assert events[1].action is Action.RIGHT
