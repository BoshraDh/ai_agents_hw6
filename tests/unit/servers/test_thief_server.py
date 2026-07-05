import asyncio

from fastmcp import Client

from cop_thief_mcp.servers.thief_server.server import mcp


def test_thief_server_name():
    assert mcp.name == "thief-server"


def test_thief_server_ping():
    async def _call() -> str:
        async with Client(mcp) as client:
            result = await client.call_tool("ping", {})
            return result.data

    assert asyncio.run(_call()) == "thief-server-ready"
