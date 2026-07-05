import asyncio

from fastmcp import Client

from cop_thief_mcp.servers.common import build_stub_server


def test_stub_server_ping_returns_configured_message():
    mcp = build_stub_server(name="test-server", ready_message="test-server-ready")

    async def _call() -> str:
        async with Client(mcp) as client:
            result = await client.call_tool("ping", {})
            return result.data

    assert asyncio.run(_call()) == "test-server-ready"


def test_stub_server_uses_given_name():
    mcp = build_stub_server(name="my-name", ready_message="ready")

    assert mcp.name == "my-name"
