import pytest

from cop_thief_mcp.services.llm.client_factory import build_openai_client


def test_raises_clearly_when_api_key_is_not_set(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_openai_client()


def test_builds_a_client_when_api_key_is_set(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")

    client = build_openai_client()

    assert client.api_key == "sk-test-not-a-real-key"
