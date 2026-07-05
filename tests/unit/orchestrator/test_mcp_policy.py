from cop_thief_mcp.orchestrator.mcp_policy import (
    build_decide_move_message_request,
    build_decide_move_request,
)
from cop_thief_mcp.services.game.grid import Grid, Position, Role
from cop_thief_mcp.services.game.sub_game import TurnContext


def test_request_includes_opponent_position_for_tactical_decisions():
    """Stage 4's heuristic/Q-table need the opponent's position to chase/flee
    meaningfully. This intentionally reverses Stage 3's "own state only" rule
    -- see docs/PRD_decision_engine.md for the trade-off this represents.
    """
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
            "opponent_row": 4,
            "opponent_col": 4,
            "grid_rows": 5,
            "grid_cols": 5,
            "barriers": [[0, 0]],
            "barriers_placed": 1,
            "max_barriers": 5,
        }
    }


def test_message_request_never_includes_opponent_position():
    """Stage 5's `llm` policy request must carry only the acting agent's own
    state and the opponent's free-text message -- never a position field.
    """
    context = TurnContext(
        role=Role.COP,
        own_position=Position(1, 2),
        opponent_position=Position(4, 4),
        grid=Grid(rows=5, cols=5),
        barriers=frozenset({Position(0, 0)}),
        moves_made=3,
        max_moves=25,
        barriers_placed=1,
        max_barriers=5,
    )

    request = build_decide_move_message_request(context, "I saw something move nearby")

    assert request == {
        "request": {
            "own_row": 1,
            "own_col": 2,
            "grid_rows": 5,
            "grid_cols": 5,
            "barriers": [[0, 0]],
            "barriers_placed": 1,
            "max_barriers": 5,
            "moves_made": 3,
            "max_moves": 25,
            "opponent_message": "I saw something move nearby",
        }
    }
    assert "opponent_row" not in request["request"]
    assert "opponent_col" not in request["request"]
