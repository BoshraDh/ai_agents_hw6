"""Holds the most recent free-text message each side has sent, for the other to
read next turn. Under the `llm` decision policy, this is the *only* channel
through which the Cop and Thief agents can learn anything about each other --
see docs/PRD_mcp_orchestration.md.
"""

from dataclasses import dataclass


@dataclass
class MessageExchange:
    cop_message: str = ""
    thief_message: str = ""
