import asyncio

import pytest

from cop_thief_mcp.servers.lifecycle import wait_for_port


def test_wait_for_port_times_out_when_nothing_is_listening():
    async def _call() -> None:
        # port 1 requires elevated privileges and nothing binds it in CI/dev environments
        await wait_for_port("127.0.0.1", 1, timeout=0.2)

    with pytest.raises(TimeoutError):
        asyncio.run(_call())
