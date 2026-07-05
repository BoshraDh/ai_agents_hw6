"""Shared FastMCP server construction, so the Cop/Thief server modules stay duplication-free."""

from fastmcp import FastMCP
from pydantic import BaseModel

from cop_thief_mcp.services.decision.dispatch import LLM, Q_LEARNING, choose_action
from cop_thief_mcp.services.decision.q_learning_training import train_q_tables
from cop_thief_mcp.services.game.grid import Grid, Position, Role
from cop_thief_mcp.services.llm.client_factory import build_openai_client
from cop_thief_mcp.services.llm.openai_agent import decide_turn
from cop_thief_mcp.shared.gatekeeper import ApiGatekeeper
from cop_thief_mcp.shared.rate_limits_config import load_rate_limits_config

_TRAINING_GRID = Grid(rows=5, cols=5)


class TurnRequest(BaseModel):
    """What an agent needs to decide its move for this turn.

    `opponent_row`/`opponent_col` are ground truth, used only by the
    heuristic/Q-table policies (Stage 4). `opponent_message` is the
    opponent's free-text message, used only by the `llm` policy (Stage 5)
    -- the LLM path never reads the ground-truth position fields, keeping
    the Dec-POMDP partial-observability boundary real even though the
    wire schema carries both for backward compatibility. See
    docs/PRD_mcp_orchestration.md.
    """

    own_row: int
    own_col: int
    grid_rows: int
    grid_cols: int
    barriers: list[tuple[int, int]] = []
    barriers_placed: int = 0
    max_barriers: int = 0
    opponent_row: int | None = None
    opponent_col: int | None = None
    moves_made: int = 0
    max_moves: int = 0
    opponent_message: str = ""


class TurnResponse(BaseModel):
    action: str
    message: str = ""


def build_agent_server(
    name: str, role: Role, ready_message: str, decision_policy: str = "heuristic"
) -> FastMCP:
    """Build a FastMCP app for one side of the game: a `ping` health-check plus a
    `decide_move` tool backed by the configured decision policy (`heuristic`
    by default; `random_walk`, `q_learning`, and `llm` are also selectable).
    """
    mcp: FastMCP = FastMCP(name)

    q_table = None
    if decision_policy == Q_LEARNING:
        cop_table, thief_table = train_q_tables(_TRAINING_GRID, max_moves=25, max_barriers=5)
        q_table = cop_table if role is Role.COP else thief_table

    openai_client = None
    gatekeeper = None
    if decision_policy == LLM:
        openai_client = build_openai_client()
        gatekeeper = ApiGatekeeper(load_rate_limits_config().for_service("openai"))

    @mcp.tool()
    def ping() -> str:
        """Health-check tool confirming this MCP server is reachable and responding."""
        return ready_message

    @mcp.tool()
    def decide_move(request: TurnRequest) -> TurnResponse:
        """Return this agent's chosen action and message for the current turn."""
        grid = Grid(rows=request.grid_rows, cols=request.grid_cols)
        position = Position(request.own_row, request.own_col)
        barriers = frozenset(Position(r, c) for r, c in request.barriers)

        if decision_policy == LLM:
            action, message = decide_turn(
                openai_client, gatekeeper, role, grid, position, barriers,
                request.barriers_placed, request.max_barriers,
                request.moves_made, request.max_moves, request.opponent_message,
            )
            return TurnResponse(action=action.value, message=message)

        opponent_position = Position(request.opponent_row, request.opponent_col)
        action = choose_action(
            decision_policy, role, grid, position, opponent_position, barriers,
            request.barriers_placed, request.max_barriers, q_table,
        )
        return TurnResponse(action=action.value, message="")

    return mcp
