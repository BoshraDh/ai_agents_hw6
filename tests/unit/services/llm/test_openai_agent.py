from unittest.mock import MagicMock

import pytest

from cop_thief_mcp.services.game.grid import Action, Grid, Position, Role
from cop_thief_mcp.services.llm.openai_agent import decide_turn, parse_llm_response
from cop_thief_mcp.shared.gatekeeper import ApiGatekeeper
from cop_thief_mcp.shared.rate_limits_config import ServiceRateLimit

FAST_LIMITS = ServiceRateLimit(requests_per_minute=1000, max_retries=1, retry_after_seconds=0)


def _fake_client(content: str) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    client.chat.completions.create.return_value = response
    return client


def test_parse_llm_response_valid():
    assert parse_llm_response('{"action": "up", "message": "hi"}') == ("up", "hi")


def test_parse_llm_response_defaults_message_to_empty():
    assert parse_llm_response('{"action": "up"}') == ("up", "")


def test_parse_llm_response_invalid_json_raises():
    with pytest.raises(Exception):  # noqa: B017 - json.JSONDecodeError, exact type not load-bearing
        parse_llm_response("not json")


def test_decide_turn_returns_legal_llm_action_and_message():
    client = _fake_client('{"action": "right", "message": "I am close"}')
    gatekeeper = ApiGatekeeper(FAST_LIMITS)
    grid = Grid(rows=5, cols=5)

    action, message = decide_turn(
        client, gatekeeper, Role.COP, grid, Position(2, 2), frozenset(), 0, 5, 0, 25, ""
    )

    assert action is Action.RIGHT
    assert message == "I am close"


def test_decide_turn_falls_back_on_illegal_action():
    client = _fake_client('{"action": "up", "message": "trying to escape upward"}')
    gatekeeper = ApiGatekeeper(FAST_LIMITS)
    grid = Grid(rows=5, cols=5)

    action, message = decide_turn(
        client, gatekeeper, Role.THIEF, grid, Position(0, 0), frozenset(), 0, 0, 0, 25, ""
    )

    assert action in {Action.DOWN, Action.RIGHT}
    assert message == ""


def test_decide_turn_falls_back_on_malformed_response():
    client = _fake_client("not valid json")
    gatekeeper = ApiGatekeeper(FAST_LIMITS)
    grid = Grid(rows=5, cols=5)

    action, message = decide_turn(
        client, gatekeeper, Role.COP, grid, Position(2, 2), frozenset(), 0, 5, 0, 25, ""
    )

    assert action in {Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT}
    assert message == ""


def test_decide_turn_falls_back_when_client_raises():
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("network error")
    gatekeeper = ApiGatekeeper(FAST_LIMITS)
    grid = Grid(rows=5, cols=5)

    action, message = decide_turn(
        client, gatekeeper, Role.COP, grid, Position(2, 2), frozenset(), 0, 5, 0, 25, ""
    )

    assert action in {Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT}
    assert message == ""


def test_decide_turn_cop_can_place_barrier():
    client = _fake_client('{"action": "place_barrier", "message": "sealing this off"}')
    gatekeeper = ApiGatekeeper(FAST_LIMITS)
    grid = Grid(rows=5, cols=5)

    action, message = decide_turn(
        client, gatekeeper, Role.COP, grid, Position(2, 2), frozenset(), 0, 5, 0, 25, ""
    )

    assert action is Action.PLACE_BARRIER
    assert message == "sealing this off"


def test_decide_turn_thief_cannot_place_barrier_falls_back():
    client = _fake_client('{"action": "place_barrier", "message": "nope"}')
    gatekeeper = ApiGatekeeper(FAST_LIMITS)
    grid = Grid(rows=5, cols=5)

    action, message = decide_turn(
        client, gatekeeper, Role.THIEF, grid, Position(2, 2), frozenset(), 0, 5, 0, 25, ""
    )

    assert action in {Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT}
    assert message == ""
