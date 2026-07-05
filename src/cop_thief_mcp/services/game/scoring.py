"""Per-sub-game scoring, per the fixed table in the task document."""

from enum import Enum

from cop_thief_mcp.shared.config import ScoringConfig


class SubGameOutcome(Enum):
    COP_WINS = "cop_wins"
    THIEF_WINS = "thief_wins"


def score_sub_game(outcome: SubGameOutcome, scoring: ScoringConfig) -> tuple[int, int]:
    """Return (cop_score, thief_score) for a single sub-game outcome."""
    if outcome is SubGameOutcome.COP_WINS:
        return scoring.cop_win_cop, scoring.cop_win_thief
    return scoring.thief_win_cop, scoring.thief_win_thief
