"""Shared FastMCP server construction, so the Cop/Thief server modules stay duplication-free."""

from fastmcp import FastMCP
from pydantic import BaseModel

from cop_thief_mcp.services.decision.random_walk import choose_random_legal_action
from cop_thief_mcp.services.game.grid import Grid, Position, Role


class TurnRequest(BaseModel):
    """What an agent needs to choose its own move: its own state only, never the opponent's.

    Omitting the opponent's position here (not just at the LLM/NL layer)
    enforces the partial-observability boundary from
    docs/PRD_game_engine.md at the transport level from the very start.
    """

    own_row: int
    own_col: int
    grid_rows: int
    grid_cols: int
    barriers: list[tuple[int, int]] = []


def build_agent_server(name: str, role: Role, ready_message: str) -> FastMCP:
    """Build a FastMCP app for one side of the game: a `ping` health-check plus a
    `decide_move` tool. Stage 3's `decide_move` uses a placeholder random-legal-move
    policy that proves the MCP wiring end-to-end; Stage 4 replaces the policy behind
    this same tool with a real heuristic/Q-table decision.
    """
    mcp: FastMCP = FastMCP(name)

    @mcp.tool()
    def ping() -> str:
        """Health-check tool confirming this MCP server is reachable and responding."""
        return ready_message

    @mcp.tool()
    def decide_move(request: TurnRequest) -> str:
        """Return this agent's chosen action name for the current turn."""
        grid = Grid(rows=request.grid_rows, cols=request.grid_cols)
        position = Position(request.own_row, request.own_col)
        barriers = frozenset(Position(r, c) for r, c in request.barriers)
        action = choose_random_legal_action(grid, position, role, barriers)
        return action.value

    return mcp
