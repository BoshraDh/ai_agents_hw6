import base64
import json
from unittest.mock import MagicMock

from cop_thief_mcp.services.reporting.gmail_sender import build_report_email, send_game_report
from cop_thief_mcp.shared.gatekeeper import ApiGatekeeper
from cop_thief_mcp.shared.rate_limits_config import ServiceRateLimit

FAST_LIMITS = ServiceRateLimit(requests_per_minute=1000, max_retries=1, retry_after_seconds=0)


def test_build_report_email_body_contains_only_the_json_report():
    report = {"totals": {"cop": 20, "thief": 5}}

    body = build_report_email(report, "someone@example.com")

    decoded = base64.urlsafe_b64decode(body["raw"]).decode()
    # The email body (after MIME headers) must be exactly the JSON, no free text.
    payload = decoded.split("\n\n", 1)[1].strip()
    assert json.loads(payload) == report
    assert "someone@example.com" in decoded


def test_send_game_report_calls_gmail_api_and_returns_message_id():
    gmail_service = MagicMock()
    gmail_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
        "id": "abc123"
    }
    gatekeeper = ApiGatekeeper(FAST_LIMITS)

    message_id = send_game_report(gmail_service, gatekeeper, "someone@example.com", {"totals": {}})

    assert message_id == "abc123"
    gmail_service.users.return_value.messages.return_value.send.assert_called_once()
    _, kwargs = gmail_service.users.return_value.messages.return_value.send.call_args
    assert kwargs["userId"] == "me"
    assert "raw" in kwargs["body"]
