"""Shared FastMCP server construction, so the Cop/Thief server modules stay duplication-free."""

from fastmcp import FastMCP
from pydantic import BaseModel

from cop_thief_mcp.services.decision.dispatch import Q_LEARNING, choose_action
from cop_thief_mcp.services.decision.q_learning_training import train_q_tables
from cop_thief_mcp.services.game.grid import Grid, Position, Role

_TRAINING_GRID = Grid(rows=5, cols=5)


class TurnRequest(BaseModel):
    """What an agent needs to decide its move for this turn.

    Includes the opponent's position as ground truth so the heuristic/
    Q-table decision policies (Stage 4) can make genuinely tactical
    chase/flee decisions. This reverses Stage 3's stricter "own state
    only, never the opponent's" rule — see docs/PRD_decision_engine.md
    for the trade-off and how Stage 5 changes the *source* of this field
    (an NL-inferred belief) without changing its presence in the wire
    contract.
    """

    own_row: int
    own_col: int
    opponent_row: int
    opponent_col: int
    grid_rows: int
    grid_cols: int
    barriers: list[tuple[int, int]] = []
    barriers_placed: int = 0
    max_barriers: int = 0


def build_agent_server(
    name: str, role: Role, ready_message: str, decision_policy: str = "heuristic"
) -> FastMCP:
    """Build a FastMCP app for one side of the game: a `ping` health-check plus a
    `decide_move` tool backed by the configured decision policy (heuristic by
    default; `random_walk` and `q_learning` are also selectable via config).
    """
    mcp: FastMCP = FastMCP(name)

    q_table = None
    if decision_policy == Q_LEARNING:
        cop_table, thief_table = train_q_tables(_TRAINING_GRID, max_moves=25, max_barriers=5)
        q_table = cop_table if role is Role.COP else thief_table

    @mcp.tool()
    def ping() -> str:
        """Health-check tool confirming this MCP server is reachable and responding."""
        return ready_message

    @mcp.tool()
    def decide_move(request: TurnRequest) -> str:
        """Return this agent's chosen action name for the current turn."""
        grid = Grid(rows=request.grid_rows, cols=request.grid_cols)
        position = Position(request.own_row, request.own_col)
        opponent_position = Position(request.opponent_row, request.opponent_col)
        barriers = frozenset(Position(r, c) for r, c in request.barriers)
        action = choose_action(
            decision_policy,
            role,
            grid,
            position,
            opponent_position,
            barriers,
            request.barriers_placed,
            request.max_barriers,
            q_table,
        )
        return action.value

    return mcp
