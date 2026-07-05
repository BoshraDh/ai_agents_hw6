from cop_thief_mcp.orchestrator.mcp_policy import build_decide_move_request
from cop_thief_mcp.services.game.grid import Grid, Position, Role
from cop_thief_mcp.services.game.sub_game import TurnContext


def test_request_includes_only_own_state_never_opponent_position():
    context = TurnContext(
        role=Role.THIEF,
        own_position=Position(1, 2),
        opponent_position=Position(4, 4),
        grid=Grid(rows=5, cols=5),
        barriers=frozenset({Position(0, 0)}),
        moves_made=3,
        max_moves=25,
        barriers_placed=1,
        max_barriers=5,
    )

    request = build_decide_move_request(context)

    assert request == {
        "request": {
            "own_row": 1,
            "own_col": 2,
            "grid_rows": 5,
            "grid_cols": 5,
            "barriers": [[0, 0]],
        }
    }
