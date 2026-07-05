"""Loads per-service rate limits from config/rate_limits.json. No hard-coded limits elsewhere."""

from dataclasses import dataclass
from pathlib import Path

from cop_thief_mcp.shared.constants import PROJECT_ROOT
from cop_thief_mcp.shared.json_loader import read_json

DEFAULT_RATE_LIMITS_CONFIG_PATH = PROJECT_ROOT / "config" / "rate_limits.json"


@dataclass(frozen=True)
class ServiceRateLimit:
    requests_per_minute: int
    max_retries: int
    retry_after_seconds: float


@dataclass(frozen=True)
class RateLimitsConfig:
    version: str
    services: dict[str, ServiceRateLimit]

    def for_service(self, name: str) -> ServiceRateLimit:
        return self.services[name]


def load_rate_limits_config(path: Path | None = None) -> RateLimitsConfig:
    """Read and validate per-service rate limits from a JSON file."""
    config_path = path or DEFAULT_RATE_LIMITS_CONFIG_PATH
    raw = read_json(config_path)

    services = {name: ServiceRateLimit(**limits) for name, limits in raw["services"].items()}
    return RateLimitsConfig(version=raw["version"], services=services)
