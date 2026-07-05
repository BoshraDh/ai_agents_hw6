import asyncio

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


def test_decide_move_returns_a_legal_movement_action():
    mcp = build_agent_server(name="test-server", role=Role.THIEF, ready_message="ready")
    request = {"own_row": 0, "own_col": 0, "grid_rows": 5, "grid_cols": 5, "barriers": []}

    result = _call_tool(mcp, "decide_move", {"request": request})

    assert result.data in {"up", "down", "left", "right", "pass"}


def test_decide_move_passes_when_boxed_in_by_barriers():
    mcp = build_agent_server(name="test-server", role=Role.THIEF, ready_message="ready")
    request = {
        "own_row": 1,
        "own_col": 1,
        "grid_rows": 3,
        "grid_cols": 3,
        "barriers": [[0, 1], [1, 0], [1, 2], [2, 1]],
    }

    result = _call_tool(mcp, "decide_move", {"request": request})

    assert result.data == "pass"


def test_decide_move_ignores_barriers_for_cop_role():
    mcp = build_agent_server(name="test-server", role=Role.COP, ready_message="ready")
    request = {
        "own_row": 1,
        "own_col": 1,
        "grid_rows": 3,
        "grid_cols": 3,
        "barriers": [[0, 1], [1, 0], [1, 2], [2, 1]],
    }

    result = _call_tool(mcp, "decide_move", {"request": request})

    assert result.data in {"up", "down", "left", "right"}
