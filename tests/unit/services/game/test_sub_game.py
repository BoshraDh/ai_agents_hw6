from cop_thief_mcp.services.game.grid import Action, Grid, Position
from cop_thief_mcp.services.game.scoring import SubGameOutcome
from cop_thief_mcp.services.game.sub_game import run_sub_game

GRID = Grid(rows=5, cols=5)


def _scripted(actions):
    """A one-shot policy: plays the given actions in order, then always PASSes."""
    queue = list(actions)

    def policy(_context):
        return queue.pop(0) if queue else Action.PASS

    return policy


def test_cop_captures_on_its_own_turn():
    result = run_sub_game(
        GRID,
        cop_start=Position(0, 0),
        thief_start=Position(0, 1),
        cop_policy=_scripted([Action.RIGHT]),
        thief_policy=_scripted([Action.PASS]),
        max_moves=25,
        max_barriers=5,
    )
    assert result.outcome is SubGameOutcome.COP_WINS
    assert result.moves_made == 1
    assert result.cop_position == Position(0, 1)


def test_capture_detected_when_thief_walks_into_cop():
    result = run_sub_game(
        GRID,
        cop_start=Position(0, 1),
        thief_start=Position(0, 0),
        cop_policy=_scripted([Action.PASS]),
        thief_policy=_scripted([Action.RIGHT]),
        max_moves=25,
        max_barriers=5,
    )
    assert result.outcome is SubGameOutcome.COP_WINS
    assert result.moves_made == 1


def test_thief_survives_full_sub_game():
    result = run_sub_game(
        GRID,
        cop_start=Position(0, 0),
        thief_start=Position(4, 4),
        cop_policy=_scripted([]),
        thief_policy=_scripted([]),
        max_moves=25,
        max_barriers=5,
    )
    assert result.outcome is SubGameOutcome.THIEF_WINS
    assert result.moves_made == 25


def test_barrier_blocks_thief_move():
    result = run_sub_game(
        GRID,
        cop_start=Position(1, 0),
        thief_start=Position(2, 0),
        cop_policy=_scripted([Action.PLACE_BARRIER, Action.PASS]),
        thief_policy=_scripted([Action.PASS, Action.UP]),
        max_moves=2,
        max_barriers=5,
    )
    assert result.outcome is SubGameOutcome.THIEF_WINS
    assert result.thief_position == Position(2, 0)
    assert Position(1, 0) in result.barriers


def test_barrier_placement_capped_at_max_barriers():
    result = run_sub_game(
        GRID,
        cop_start=Position(0, 0),
        thief_start=Position(4, 4),
        cop_policy=_scripted([Action.PLACE_BARRIER, Action.PLACE_BARRIER]),
        thief_policy=_scripted([]),
        max_moves=2,
        max_barriers=1,
    )
    assert len(result.barriers) == 1
    assert result.cop_position == Position(0, 0)
