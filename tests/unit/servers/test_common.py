import asyncio
from unittest.mock import MagicMock, patch

from fastmcp import Client

from cop_thief_mcp.servers.common import build_agent_server
from cop_thief_mcp.services.game.grid import Role


def _call_tool(mcp, tool_name: str, arguments: dict):
    async def _call():
        async with Client(mcp) as client:
            return await client.call_tool(tool_name, arguments)

    return asyncio.run(_call())


def test_agent_server_ping_returns_configured_message():
    mcp = build_agent_server(name="test-server", role=Role.COP, ready_message="test-server-ready")

    assert _call_tool(mcp, "ping", {}).data == "test-server-ready"


def test_agent_server_uses_given_name():
    mcp = build_agent_server(name="my-name", role=Role.COP, ready_message="ready")

    assert mcp.name == "my-name"


def test_decide_move_defaults_to_heuristic_and_chases_the_thief():
    mcp = build_agent_server(name="test-server", role=Role.COP, ready_message="ready")
    request = {
        "own_row": 2,
        "own_col": 2,
        "opponent_row": 2,
        "opponent_col": 4,
        "grid_rows": 5,
        "grid_cols": 5,
        "barriers": [],
    }

    result = _call_tool(mcp, "decide_move", {"request": request})

    assert result.data.action == "right"
    assert result.data.message == ""


def test_decide_move_random_walk_policy_returns_a_legal_action():
    mcp = build_agent_server(
        name="test-server", role=Role.THIEF, ready_message="ready", decision_policy="random_walk"
    )
    request = {
        "own_row": 0,
        "own_col": 0,
        "opponent_row": 4,
        "opponent_col": 4,
        "grid_rows": 5,
        "grid_cols": 5,
        "barriers": [],
    }

    result = _call_tool(mcp, "decide_move", {"request": request})

    assert result.data.action in {"up", "down", "left", "right", "pass"}


def test_decide_move_q_learning_policy_returns_a_legal_action():
    mcp = build_agent_server(
        name="test-server", role=Role.THIEF, ready_message="ready", decision_policy="q_learning"
    )
    request = {
        "own_row": 4,
        "own_col": 4,
        "opponent_row": 0,
        "opponent_col": 0,
        "grid_rows": 5,
        "grid_cols": 5,
        "barriers": [],
    }

    result = _call_tool(mcp, "decide_move", {"request": request})

    assert result.data.action in {"up", "down", "left", "right", "pass"}


def test_decide_move_thief_flees_from_cop_by_default():
    mcp = build_agent_server(name="test-server", role=Role.THIEF, ready_message="ready")
    request = {
        "own_row": 2,
        "own_col": 2,
        "opponent_row": 2,
        "opponent_col": 0,
        "grid_rows": 5,
        "grid_cols": 5,
        "barriers": [],
    }

    result = _call_tool(mcp, "decide_move", {"request": request})

    # UP, DOWN, and RIGHT all tie for max distance+mobility from an open
    # center cell; UP wins as the first-encountered tie per MOVE_ACTIONS order.
    assert result.data.action == "up"


def _fake_openai_client(content: str) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    client.chat.completions.create.return_value = response
    return client


def test_decide_move_llm_policy_uses_opponent_message_not_ground_truth():
    fake_client = _fake_openai_client('{"action": "left", "message": "heading west"}')

    with patch("cop_thief_mcp.servers.common.build_openai_client", return_value=fake_client):
        mcp = build_agent_server(
            name="test-server", role=Role.THIEF, ready_message="ready", decision_policy="llm"
        )
        request = {
            "own_row": 2,
            "own_col": 2,
            "grid_rows": 5,
            "grid_cols": 5,
            "barriers": [],
            "opponent_message": "I'm on the far side of the board",
        }

        result = _call_tool(mcp, "decide_move", {"request": request})

    assert result.data.action == "left"
    assert result.data.message == "heading west"


def test_decide_move_llm_policy_falls_back_when_response_is_malformed():
    fake_client = _fake_openai_client("not valid json")

    with patch("cop_thief_mcp.servers.common.build_openai_client", return_value=fake_client):
        mcp = build_agent_server(
            name="test-server", role=Role.COP, ready_message="ready", decision_policy="llm"
        )
        request = {"own_row": 2, "own_col": 2, "grid_rows": 5, "grid_cols": 5, "barriers": []}

        result = _call_tool(mcp, "decide_move", {"request": request})

    assert result.data.action in {"up", "down", "left", "right", "pass"}
    assert result.data.message == ""
