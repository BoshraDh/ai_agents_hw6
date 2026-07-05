from cop_thief_mcp.shared.rate_limits_config import load_rate_limits_config


def test_load_rate_limits_config_reads_default_file():
    config = load_rate_limits_config()

    assert config.version == "1.00"
    openai_limits = config.for_service("openai")
    assert openai_limits.requests_per_minute == 30
    assert openai_limits.max_retries == 3
    assert openai_limits.retry_after_seconds == 5
