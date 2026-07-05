"""Builds a synchronous Policy (for the Stage 1 engine) backed by an MCP `decide_move` call.

Only the acting agent's own position, the grid, and barriers are sent to
its server — never the opponent's position — enforcing the
partial-observability boundary from docs/PRD_game_engine.md at the
transport level.
"""

from fastmcp import Client

from cop_thief_mcp.services.game.grid import Action
from cop_thief_mcp.services.game.sub_game import Policy, TurnContext
from cop_thief_mcp.shared.async_bridge import AsyncBridge


def build_decide_move_request(context: TurnContext) -> dict:
    """Extract only what the acting agent may legitimately know about itself and the board."""
    return {
        "request": {
            "own_row": context.own_position.row,
            "own_col": context.own_position.col,
            "grid_rows": context.grid.rows,
            "grid_cols": context.grid.cols,
            "barriers": [[p.row, p.col] for p in context.barriers],
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
