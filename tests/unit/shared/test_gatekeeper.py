from unittest.mock import patch

import pytest

from cop_thief_mcp.shared.gatekeeper import ApiGatekeeper
from cop_thief_mcp.shared.rate_limits_config import ServiceRateLimit


def test_execute_returns_the_call_result():
    gatekeeper = ApiGatekeeper(ServiceRateLimit(requests_per_minute=100, max_retries=1, retry_after_seconds=0))

    result = gatekeeper.execute(lambda a, b: a + b, 2, 3)

    assert result == 5


def test_execute_retries_transient_failures_then_succeeds():
    gatekeeper = ApiGatekeeper(ServiceRateLimit(requests_per_minute=100, max_retries=3, retry_after_seconds=0))
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("transient failure")
        return "ok"

    assert gatekeeper.execute(flaky) == "ok"
    assert calls["count"] == 2


def test_execute_raises_after_exhausting_retries():
    gatekeeper = ApiGatekeeper(ServiceRateLimit(requests_per_minute=100, max_retries=2, retry_after_seconds=0))

    def always_fails():
        raise RuntimeError("permanent failure")

    with pytest.raises(RuntimeError, match="permanent failure"):
        gatekeeper.execute(always_fails)


def test_wait_for_capacity_sleeps_once_the_per_minute_limit_is_reached():
    gatekeeper = ApiGatekeeper(ServiceRateLimit(requests_per_minute=1, max_retries=1, retry_after_seconds=0))

    fake_time = [1000.0]
    sleep_calls: list[float] = []

    def fake_monotonic() -> float:
        return fake_time[0]

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        fake_time[0] += seconds

    with (
        patch("cop_thief_mcp.shared.gatekeeper.time.monotonic", side_effect=fake_monotonic),
        patch("cop_thief_mcp.shared.gatekeeper.time.sleep", side_effect=fake_sleep),
    ):
        gatekeeper.execute(lambda: None)
        gatekeeper.execute(lambda: None)

    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(60.0, abs=0.01)


def test_wait_for_capacity_does_not_sleep_once_old_calls_expire():
    gatekeeper = ApiGatekeeper(ServiceRateLimit(requests_per_minute=1, max_retries=1, retry_after_seconds=0))

    fake_time = [1000.0]
    sleep_calls: list[float] = []

    def fake_monotonic() -> float:
        return fake_time[0]

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    with (
        patch("cop_thief_mcp.shared.gatekeeper.time.monotonic", side_effect=fake_monotonic),
        patch("cop_thief_mcp.shared.gatekeeper.time.sleep", side_effect=fake_sleep),
    ):
        gatekeeper.execute(lambda: None)
        fake_time[0] += 61  # simulate the rate-limit window fully expiring
        gatekeeper.execute(lambda: None)

    assert sleep_calls == []
