"""Start/stop a FastMCP HTTP server as a background asyncio task.

Shared by the Stage 2 transport integration test and the Stage 3
orchestrator, so "run a server in the background and wait until it's
reachable" is implemented exactly once.
"""

import asyncio
import contextlib

from fastmcp import FastMCP


async def wait_for_port(host: str, port: int, timeout: float = 5.0) -> None:
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


async def start_http_server(mcp: FastMCP, host: str, port: int) -> asyncio.Task:
    """Start `mcp` over HTTP in the background and return once it accepts connections."""
    task = asyncio.create_task(mcp.run_async(transport="http", host=host, port=port, show_banner=False))
    await wait_for_port(host, port)
    return task


async def stop_server(task: asyncio.Task) -> None:
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
