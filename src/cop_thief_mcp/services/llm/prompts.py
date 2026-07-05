"""Builds the system/user prompts for the LLM-backed Cop/Thief agents.

Deliberately excludes the opponent's true position -- only what the agent
legitimately knows (its own state) and the opponent's last free-text
message are exposed here, matching the task doc's Dec-POMDP partial-
observability design. See docs/PRD_mcp_orchestration.md.
"""

from cop_thief_mcp.services.game.grid import Role

_ROLE_BRIEF = {
    Role.COP: "You are the COP. You win by moving onto the Thief's exact cell (capture).",
    Role.THIEF: "You are the THIEF. You win by surviving until moves run out without being caught.",
}


def build_system_prompt(role: Role) -> str:
    return (
        "You are playing a pursuit game on a 2D grid against another AI agent. "
        f"{_ROLE_BRIEF[role]} "
        "You can never see your opponent's exact location directly -- the ONLY "
        "information you have about them is whatever they choose to say to you "
        "in free natural language each turn. They may be honest, vague, or lying. "
        "Use their message and your own reasoning to decide your move, and write "
        "your own free-text message for them to read on their next turn (you may "
        "reveal, hint at, or bluff about your own position). "
        'Respond with a single JSON object: {"action": one of '
        '"up", "down", "left", "right", "pass", "place_barrier", '
        '"message": "<text for the opponent>"}. '
        "Only the Cop may use place_barrier, which blocks the Thief (not the "
        "Cop) from re-entering your current cell after you leave it."
    )


def build_user_prompt(
    own_row: int,
    own_col: int,
    grid_rows: int,
    grid_cols: int,
    barriers: list[tuple[int, int]],
    barriers_placed: int,
    max_barriers: int,
    moves_made: int,
    max_moves: int,
    opponent_message: str,
) -> str:
    barriers_text = ", ".join(f"({r},{c})" for r, c in barriers) or "none"
    last_message = opponent_message or "(no message yet -- this is the first turn)"
    return (
        f"Grid size: {grid_rows}x{grid_cols} (rows/cols indexed from 0).\n"
        f"Your position: ({own_row},{own_col}).\n"
        f"Barriers on the board: {barriers_text}.\n"
        f"Barriers you've placed so far: {barriers_placed}/{max_barriers}.\n"
        f"Moves so far this sub-game: {moves_made}/{max_moves}.\n"
        f'Opponent\'s last message to you: "{last_message}"\n'
        "What is your action and your message to the opponent?"
    )
