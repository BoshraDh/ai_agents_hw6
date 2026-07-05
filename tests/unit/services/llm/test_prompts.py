import inspect

from cop_thief_mcp.services.game.grid import Role
from cop_thief_mcp.services.llm.prompts import build_system_prompt, build_user_prompt


def test_system_prompt_differs_by_role():
    cop_prompt = build_system_prompt(Role.COP)
    thief_prompt = build_system_prompt(Role.THIEF)

    assert "COP" in cop_prompt
    assert "THIEF" in thief_prompt
    assert cop_prompt != thief_prompt


def test_build_user_prompt_has_no_opponent_position_parameters():
    # Structural guard: the prompt builder must never be given the
    # opponent's true position -- only its own state and the opponent's
    # free-text message. See docs/PRD_mcp_orchestration.md.
    params = set(inspect.signature(build_user_prompt).parameters)

    assert "opponent_row" not in params
    assert "opponent_col" not in params
    assert "opponent_message" in params


def test_build_user_prompt_includes_own_state_and_message():
    prompt = build_user_prompt(
        own_row=2, own_col=3, grid_rows=5, grid_cols=5,
        barriers=[(0, 0)], barriers_placed=1, max_barriers=5,
        moves_made=4, max_moves=25, opponent_message="I'm near the edge",
    )

    assert "(2,3)" in prompt
    assert "5x5" in prompt
    assert "(0,0)" in prompt
    assert "1/5" in prompt
    assert "4/25" in prompt
    assert "I'm near the edge" in prompt


def test_build_user_prompt_placeholder_for_no_message_yet():
    prompt = build_user_prompt(
        own_row=0, own_col=0, grid_rows=5, grid_cols=5,
        barriers=[], barriers_placed=0, max_barriers=5,
        moves_made=0, max_moves=25, opponent_message="",
    )

    assert "no message yet" in prompt
    assert "none" in prompt
