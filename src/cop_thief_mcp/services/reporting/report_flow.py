"""Ties together building and sending the end-of-series report."""

from cop_thief_mcp.services.game.game_series import GameSeriesResult
from cop_thief_mcp.services.reporting.game_report import build_game_report
from cop_thief_mcp.services.reporting.gmail_client import build_gmail_service
from cop_thief_mcp.services.reporting.gmail_sender import send_game_report
from cop_thief_mcp.shared.config import GameConfig
from cop_thief_mcp.shared.gatekeeper import ApiGatekeeper
from cop_thief_mcp.shared.mcp_config import McpServersConfig
from cop_thief_mcp.shared.rate_limits_config import load_rate_limits_config


def send_series_report(
    result: GameSeriesResult, game_config: GameConfig, servers_config: McpServersConfig
) -> str:
    """Build the Internal Game JSON report and email it to `game_config.report_recipient`."""
    report = build_game_report(result, game_config, servers_config)
    gmail_service = build_gmail_service()
    gatekeeper = ApiGatekeeper(load_rate_limits_config().for_service("gmail"))
    return send_game_report(gmail_service, gatekeeper, game_config.report_recipient, report)
