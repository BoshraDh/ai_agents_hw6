"""Proves the Cop and Thief FastMCP servers run as independent processes on separate ports.

Uses dedicated test ports (not the configured production ports) so this test
never collides with a real running instance.
"""

import asyncio
import contextlib

from fastmcp import Client

from cop_thief_mcp.servers.cop_server.server import mcp as cop_mcp
from cop_thief_mcp.servers.thief_server.server import mcp as thief_mcp

HOST = "127.0.0.1"
COP_TEST_PORT = 8091
THIEF_TEST_PORT = 8092


async def _wait_for_port(host: str, port: int, timeout: float = 5.0) -> None:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while True:
        try:
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            if loop.time() > deadline:
                raise TimeoutError(f"server on {host}:{port} did not start in time") from None
            await asyncio.sleep(0.05)


async def _stop(task: asyncio.Task) -> None:
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def _run_scenario() -> tuple[str, str]:
    cop_task = asyncio.create_task(
        cop_mcp.run_async(transport="http", host=HOST, port=COP_TEST_PORT, show_banner=False)
    )
    thief_task = asyncio.create_task(
        thief_mcp.run_async(transport="http", host=HOST, port=THIEF_TEST_PORT, show_banner=False)
    )
    try:
        await _wait_for_port(HOST, COP_TEST_PORT)
        await _wait_for_port(HOST, THIEF_TEST_PORT)

        async with Client(f"http://{HOST}:{COP_TEST_PORT}/mcp") as cop_client:
            cop_result = await cop_client.call_tool("ping", {})
        async with Client(f"http://{HOST}:{THIEF_TEST_PORT}/mcp") as thief_client:
            thief_result = await thief_client.call_tool("ping", {})

        return cop_result.data, thief_result.data
    finally:
        await _stop(cop_task)
        await _stop(thief_task)


def test_cop_and_thief_servers_respond_independently_over_http():
    cop_response, thief_response = asyncio.run(_run_scenario())

    assert cop_response == "cop-server-ready"
    assert thief_response == "thief-server-ready"
