"""Sends the Internal Game JSON report as a Gmail message via the centralized
API gatekeeper. Per the task doc, the email body must contain ONLY the JSON
report -- no free text.
"""

import base64
import json
from email.mime.text import MIMEText

from googleapiclient.discovery import Resource

from cop_thief_mcp.shared.gatekeeper import ApiGatekeeper

_SUBJECT = "Cop vs Thief -- Game Series Report"


def build_report_email(report: dict, recipient: str) -> dict:
    """Build the Gmail API 'raw' message body: subject line, JSON-only content."""
    message = MIMEText(json.dumps(report, indent=2))
    message["to"] = recipient
    message["subject"] = _SUBJECT
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_game_report(
    gmail_service: Resource, gatekeeper: ApiGatekeeper, recipient: str, report: dict
) -> str:
    """Send `report` as the entire email body to `recipient`; returns the sent message id."""
    body = build_report_email(report, recipient)

    def _send():
        return gmail_service.users().messages().send(userId="me", body=body).execute()

    sent = gatekeeper.execute(_send)
    return sent["id"]
