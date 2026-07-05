"""Runs a background asyncio event loop so synchronous code can call async MCP clients.

The Stage 1 game engine (`run_sub_game`/`run_game_series`) is deliberately
synchronous and untouched; this bridge lets its `Policy` callables reach
into FastMCP's async `Client` without turning the engine itself async.
"""

import asyncio
import threading
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


class AsyncBridge:
    """Owns a background event loop thread; runs coroutines submitted from sync code."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro: Awaitable[T]) -> T:
        """Schedule `coro` on the background loop and block until it completes."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def close(self, timeout: float = 5.0) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=timeout)
