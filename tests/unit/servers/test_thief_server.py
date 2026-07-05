import asyncio

from fastmcp import Client

from cop_thief_mcp.servers.thief_server.server import mcp


def _call_tool(tool_name: str, arguments: dict):
    async def _call():
        async with Client(mcp) as client:
            return await client.call_tool(tool_name, arguments)

    return asyncio.run(_call())


def test_thief_server_name():
    assert mcp.name == "thief-server"


def test_thief_server_ping():
    assert _call_tool("ping", {}).data == "thief-server-ready"


def test_thief_server_decide_move_returns_legal_action():
    request = {"own_row": 2, "own_col": 2, "grid_rows": 5, "grid_cols": 5, "barriers": []}

    result = _call_tool("decide_move", {"request": request})

    assert result.data in {"up", "down", "left", "right", "pass"}
