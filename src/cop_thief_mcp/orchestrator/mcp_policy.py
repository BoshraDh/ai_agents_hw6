"""Builds synchronous Policies (for the Stage 1 engine) backed by MCP `decide_move` calls.

Two flavors:
- `build_mcp_policy`: sends the opponent's true position (Stage 4's
  heuristic/Q-table policies). See docs/PRD_decision_engine.md.
- `build_mcp_message_policy`: sends only the opponent's last free-text
  message (Stage 5's `llm` policy) via a shared `MessageExchange` --
  never the opponent's true position. See docs/PRD_mcp_orchestration.md.
"""

from fastmcp import Client

from cop_thief_mcp.orchestrator.message_exchange import MessageExchange
from cop_thief_mcp.services.game.grid import Action, Role
from cop_thief_mcp.services.game.sub_game import Policy, TurnContext
from cop_thief_mcp.shared.async_bridge import AsyncBridge


def build_decide_move_request(context: TurnContext) -> dict:
    """Serialize a TurnContext into the decide_move tool's ground-truth wire request."""
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
                return result.data.action

        return Action(bridge.run(_call()))

    return policy


def build_decide_move_message_request(context: TurnContext, opponent_message: str) -> dict:
    """Serialize a TurnContext into the `llm` policy's wire request: own state
    plus the opponent's last free-text message -- never the true position.
    """
    return {
        "request": {
            "own_row": context.own_position.row,
            "own_col": context.own_position.col,
            "grid_rows": context.grid.rows,
            "grid_cols": context.grid.cols,
            "barriers": [[p.row, p.col] for p in context.barriers],
            "barriers_placed": context.barriers_placed,
            "max_barriers": context.max_barriers,
            "moves_made": context.moves_made,
            "max_moves": context.max_moves,
            "opponent_message": opponent_message,
        }
    }


def build_mcp_message_policy(
    server_url: str, bridge: AsyncBridge, exchange: MessageExchange, role: Role
) -> Policy:
    """Return a Policy that exchanges free-text messages with the opponent via MCP,
    instead of sharing ground-truth positions.
    """

    def policy(context: TurnContext) -> Action:
        incoming_message = exchange.thief_message if role is Role.COP else exchange.cop_message

        async def _call():
            async with Client(server_url) as client:
                result = await client.call_tool(
                    "decide_move", build_decide_move_message_request(context, incoming_message)
                )
                return result.data

        response = bridge.run(_call())
        if role is Role.COP:
            exchange.cop_message = response.message
        else:
            exchange.thief_message = response.message
        return Action(response.action)

    return policy
