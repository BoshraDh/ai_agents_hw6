"""Calls OpenAI (through the centralized gatekeeper) to decide a turn and a message.

Falls back to a random legal move (with an empty message) if the API call
fails or the response can't be parsed into a legal action -- the game must
never break because of a malformed or unavailable LLM response.
"""

import json

from openai import OpenAI

from cop_thief_mcp.services.decision.random_walk import choose_random_legal_action
from cop_thief_mcp.services.game.grid import MOVE_ACTIONS, Action, Grid, Position, Role
from cop_thief_mcp.services.game.rules import can_place_barrier, is_move_legal
from cop_thief_mcp.services.llm.prompts import build_system_prompt, build_user_prompt
from cop_thief_mcp.shared.gatekeeper import ApiGatekeeper

MODEL = "gpt-4o-mini"


def parse_llm_response(content: str) -> tuple[str, str]:
    """Parse the model's JSON reply into (action_name, message); raises ValueError."""
    data = json.loads(content)
    action_name, message = data["action"], data.get("message", "")
    if not isinstance(action_name, str) or not isinstance(message, str):
        raise ValueError("malformed LLM response: action/message must be strings")
    return action_name, message


def _is_legal(
    grid: Grid,
    position: Position,
    role: Role,
    barriers: frozenset[Position],
    barriers_placed: int,
    max_barriers: int,
    action: Action,
) -> bool:
    if action in MOVE_ACTIONS:
        return is_move_legal(grid, position, action, role, barriers)
    if action is Action.PLACE_BARRIER:
        return can_place_barrier(role, barriers_placed, max_barriers)
    return action is Action.PASS


def decide_turn(
    client: OpenAI,
    gatekeeper: ApiGatekeeper,
    role: Role,
    grid: Grid,
    position: Position,
    barriers: frozenset[Position],
    barriers_placed: int,
    max_barriers: int,
    moves_made: int,
    max_moves: int,
    opponent_message: str,
) -> tuple[Action, str]:
    """Ask the LLM for this turn's action and message; fall back to a random
    legal move (empty message) on any failure."""
    system_prompt = build_system_prompt(role)
    user_prompt = build_user_prompt(
        position.row, position.col, grid.rows, grid.cols,
        [(p.row, p.col) for p in barriers], barriers_placed, max_barriers,
        moves_made, max_moves, opponent_message,
    )

    def _call():
        return client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

    try:
        response = gatekeeper.execute(_call)
        action_name, message = parse_llm_response(response.choices[0].message.content)
        action = Action(action_name)
        if not _is_legal(grid, position, role, barriers, barriers_placed, max_barriers, action):
            raise ValueError(f"LLM chose an illegal action: {action_name}")
        return action, message
    except Exception:
        return choose_random_legal_action(grid, position, role, barriers), ""
