from cop_thief_mcp.services.game.scoring import SubGameOutcome, score_sub_game
from cop_thief_mcp.shared.config import ScoringConfig

SCORING = ScoringConfig(cop_win_cop=20, cop_win_thief=5, thief_win_cop=5, thief_win_thief=10)


def test_score_cop_wins():
    assert score_sub_game(SubGameOutcome.COP_WINS, SCORING) == (20, 5)


def test_score_thief_wins():
    assert score_sub_game(SubGameOutcome.THIEF_WINS, SCORING) == (5, 10)
