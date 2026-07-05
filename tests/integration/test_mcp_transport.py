"""Proves the Cop and Thief FastMCP servers run as independent processes on separate ports.

Uses dedicated test ports (not the configured production ports) so this test
never collides with a real running instance.
"""

import asyncio

from fastmcp import Client

from cop_thief_mcp.servers.cop_server.server import mcp as cop_mcp
from cop_thief_mcp.servers.lifecycle import start_http_server, stop_server
from cop_thief_mcp.servers.thief_server.server import mcp as thief_mcp

HOST = "127.0.0.1"
COP_TEST_PORT = 8091
THIEF_TEST_PORT = 8092


async def _run_scenario() -> tuple[str, str]:
    cop_task = await start_http_server(cop_mcp, HOST, COP_TEST_PORT)
    thief_task = await start_http_server(thief_mcp, HOST, THIEF_TEST_PORT)
    try:
        async with Client(f"http://{HOST}:{COP_TEST_PORT}/mcp") as cop_client:
            cop_result = await cop_client.call_tool("ping", {})
        async with Client(f"http://{HOST}:{THIEF_TEST_PORT}/mcp") as thief_client:
            thief_result = await thief_client.call_tool("ping", {})

        return cop_result.data, thief_result.data
    finally:
        await stop_server(cop_task)
        await stop_server(thief_task)


def test_cop_and_thief_servers_respond_independently_over_http():
    cop_response, thief_response = asyncio.run(_run_scenario())

    assert cop_response == "cop-server-ready"
    assert thief_response == "thief-server-ready"
