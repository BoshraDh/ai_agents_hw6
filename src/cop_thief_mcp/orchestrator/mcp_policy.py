"""Builds a synchronous Policy (for the Stage 1 engine) backed by an MCP `decide_move` call.

The request includes the opponent's true position, grid, and barrier
state, so Stage 4's heuristic/Q-table decision policies can make
genuinely tactical chase/flee decisions. See docs/PRD_decision_engine.md
for why this reverses Stage 3's "own state only" rule, and how Stage 5
changes the *source* of the opponent-position field (an NL-inferred
belief instead of ground truth) without changing the wire contract.
"""

from fastmcp import Client

from cop_thief_mcp.services.game.grid import Action
from cop_thief_mcp.services.game.sub_game import Policy, TurnContext
from cop_thief_mcp.shared.async_bridge import AsyncBridge


def build_decide_move_request(context: TurnContext) -> dict:
    """Serialize a TurnContext into the decide_move tool's wire request."""
    return {
        "request": {
            "own_row": context.own_position.row,
            "own_col": context.own_position.col,
            "opponent_row": context.opponent_position.row,
            "opponent_col": context.opponent_position.col,
            "grid_rows": context.grid.rows,
            "grid_cols": context.grid.cols,
            "barriers": [[p.row, p.col] for p in context.barriers],
            "barriers_placed": context.barriers_placed,
            "max_barriers": context.max_barriers,
        }
    }


def build_mcp_policy(server_url: str, bridge: AsyncBridge) -> Policy:
    """Return a Policy that asks the agent's own MCP server to `decide_move` each turn."""

    def policy(context: TurnContext) -> Action:
        async def _call() -> str:
            async with Client(server_url) as client:
                result = await client.call_tool("decide_move", build_decide_move_request(context))
                return result.data

        return Action(bridge.run(_call()))

    return policy
