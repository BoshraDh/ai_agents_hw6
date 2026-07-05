"""Centralized rate-limited, retried, logged wrapper for every external API call.

Per the submission guidelines: no external API call (OpenAI, Gmail, ...) may
bypass this gatekeeper. Limits are config-driven (rate_limits_config.py),
never hard-coded.
"""

import logging
import time
from collections import deque
from collections.abc import Callable
from threading import Lock
from typing import TypeVar

from cop_thief_mcp.shared.rate_limits_config import ServiceRateLimit

T = TypeVar("T")
logger = logging.getLogger(__name__)


class ApiGatekeeper:
    """Enforces a requests-per-minute cap and retries transient failures for one service."""

    def __init__(self, limits: ServiceRateLimit) -> None:
        self._limits = limits
        self._call_times: deque[float] = deque()
        self._lock = Lock()

    def _wait_for_capacity(self) -> None:
        with self._lock:
            now = time.monotonic()
            while self._call_times and now - self._call_times[0] > 60:
                self._call_times.popleft()
            if len(self._call_times) >= self._limits.requests_per_minute:
                sleep_time = 60 - (now - self._call_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            self._call_times.append(time.monotonic())

    def execute(self, api_call: Callable[..., T], *args, **kwargs) -> T:
        """Run `api_call` under the rate limit, retrying transient failures."""
        self._wait_for_capacity()
        last_error: Exception | None = None
        for attempt in range(1, self._limits.max_retries + 1):
            try:
                logger.info("gatekeeper: calling %s (attempt %d)", getattr(api_call, "__name__", api_call), attempt)
                return api_call(*args, **kwargs)
            except Exception as exc:  # deliberately broad: retry any transient failure
                last_error = exc
                logger.warning("gatekeeper: call failed (attempt %d): %s", attempt, exc)
                if attempt < self._limits.max_retries:
                    time.sleep(self._limits.retry_after_seconds)
        assert last_error is not None
        raise last_error
