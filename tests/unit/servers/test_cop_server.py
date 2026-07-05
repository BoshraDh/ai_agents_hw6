import asyncio

from fastmcp import Client

from cop_thief_mcp.servers.cop_server.server import mcp


def test_cop_server_name():
    assert mcp.name == "cop-server"


def test_cop_server_ping():
    async def _call() -> str:
        async with Client(mcp) as client:
            result = await client.call_tool("ping", {})
            return result.data

    assert asyncio.run(_call()) == "cop-server-ready"
