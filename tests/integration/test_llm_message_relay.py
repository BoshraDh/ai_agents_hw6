"""Proves the `llm` policy's free-text message exchange actually round-trips
through real MCP HTTP calls: what one side says arrives as the other's
`opponent_message` on its next turn. The OpenAI client itself is mocked
(no real API calls/costs) -- only the MCP transport is real.
"""

from unittest.mock import MagicMock, patch

from cop_thief_mcp.orchestrator.mcp_policy import build_mcp_message_policy
from cop_thief_mcp.orchestrator.message_exchange import MessageExchange
from cop_thief_mcp.servers.common import build_agent_server
from cop_thief_mcp.servers.lifecycle import start_http_server, stop_server
from cop_thief_mcp.services.game.grid import Grid, Position, Role
from cop_thief_mcp.services.game.sub_game import run_sub_game
from cop_thief_mcp.shared.async_bridge import AsyncBridge

HOST = "127.0.0.1"
COP_TEST_PORT = 8097
THIEF_TEST_PORT = 8098


def _fake_client(response_content: str, seen_prompts: list[str]) -> MagicMock:
    client = MagicMock()

    def _create(model, messages, response_format):
        seen_prompts.append(messages[-1]["content"])
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content=response_content))]
        return response

    client.chat.completions.create.side_effect = _create
    return client


def test_opponent_message_relayed_across_a_full_turn_cycle():
    cop_prompts: list[str] = []
    thief_prompts: list[str] = []
    cop_client = _fake_client('{"action": "pass", "message": "I am guarding the north exit"}', cop_prompts)
    thief_client = _fake_client('{"action": "pass", "message": "I am hiding somewhere quiet"}', thief_prompts)

    with patch("cop_thief_mcp.servers.common.build_openai_client", side_effect=[cop_client, thief_client]):
        cop_mcp = build_agent_server(name="cop-server", role=Role.COP, ready_message="ready", decision_policy="llm")
        thief_mcp = build_agent_server(
            name="thief-server", role=Role.THIEF, ready_message="ready", decision_policy="llm"
        )

    bridge = AsyncBridge()
    try:
        cop_task = bridge.run(start_http_server(cop_mcp, HOST, COP_TEST_PORT))
        thief_task = bridge.run(start_http_server(thief_mcp, HOST, THIEF_TEST_PORT))
        try:
            exchange = MessageExchange()
            cop_policy = build_mcp_message_policy(f"http://{HOST}:{COP_TEST_PORT}/mcp", bridge, exchange, Role.COP)
            thief_policy = build_mcp_message_policy(
                f"http://{HOST}:{THIEF_TEST_PORT}/mcp", bridge, exchange, Role.THIEF
            )

            grid = Grid(rows=5, cols=5)
            run_sub_game(
                grid, Position(0, 0), Position(4, 4), cop_policy, thief_policy, max_moves=1, max_barriers=5
            )

            assert exchange.cop_message == "I am guarding the north exit"
            assert exchange.thief_message == "I am hiding somewhere quiet"
            assert "no message yet" in thief_prompts[0]
            assert "I am hiding somewhere quiet" in cop_prompts[0]
        finally:
            bridge.run(stop_server(cop_task))
            bridge.run(stop_server(thief_task))
    finally:
        bridge.close()
