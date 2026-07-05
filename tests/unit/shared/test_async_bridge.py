import asyncio

from cop_thief_mcp.shared.async_bridge import AsyncBridge


def test_run_executes_coroutine_and_returns_result():
    bridge = AsyncBridge()
    try:

        async def _add(a: int, b: int) -> int:
            return a + b

        assert bridge.run(_add(2, 3)) == 5
    finally:
        bridge.close()


def test_run_can_be_called_multiple_times_sequentially():
    bridge = AsyncBridge()
    try:

        async def _sleep_and_return(value: str) -> str:
            await asyncio.sleep(0)
            return value

        assert bridge.run(_sleep_and_return("first")) == "first"
        assert bridge.run(_sleep_and_return("second")) == "second"
    finally:
        bridge.close()
