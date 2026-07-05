# PRD — Game Engine (Stage 1)

## Purpose

A pure, I/O-free implementation of the Cop-vs-Thief pursuit game's rules,
independent of MCP, LLMs, or any decision-making strategy. This is the
foundation every later stage (MCP transport, orchestrator, decision
policies, NL protocol) builds on without ever re-implementing game rules.

## Formal model

- **State space `S`**: `(cop_position, thief_position, barriers, moves_made)`
  for the active sub-game.
- **Action space `A`**: `{UP, DOWN, LEFT, RIGHT, PASS, PLACE_BARRIER}` per
  `cop_thief_mcp.services.game.grid.Action`. `PLACE_BARRIER` is only
  meaningful for the Cop.
- **Transition function `P`**: deterministic — `services/game/sub_game.py`
  `_resolve_turn` applies an action to a position, rejecting moves that
  leave the grid or (for the Thief) land on a barrier cell.
- **Reward function `R`**: `services/game/scoring.py` `score_sub_game`,
  config-driven via `ScoringConfig` (defaults: Cop win 20/5, Thief win 5/10).
- **Observation space / function**: intentionally **not implemented here**.
  Stage 1's `Policy` callables receive the *full* `TurnContext` (true
  positions of both sides) because they are scripted test doubles used to
  exercise engine mechanics, not real agents. Restricting what a real agent
  observes (partial observability via the NL channel only) is an
  orchestrator-level concern introduced in Stage 5 — see
  `docs/PRD_mcp_orchestration.md` (to be written in that stage).
- **Discount factor `γ`**: not applicable at this stage (no learning yet);
  relevant once Stage 4's optional Q-learning policy is implemented.

## Design decisions

- **Turn order**: Thief moves first each round, then Cop, per the task
  document. Implemented as the outer loop in `run_sub_game` iterating
  `range(max_moves)`, resolving Thief then Cop per iteration.
- **Capture is symmetric**: `is_capture` simply checks
  `cop_position == thief_position`, regardless of whose move caused the
  coincidence (covers both "Cop walks onto Thief" and "Thief walks into
  Cop" — both are a capture per the task doc's win condition).
- **Illegal actions are no-ops, not errors**: if a policy returns an
  illegal action (out of bounds, barrier-blocked, or an over-the-limit
  `PLACE_BARRIER`), the engine keeps the actor in place rather than
  raising. This keeps the engine tolerant of imperfect upstream
  decision-makers (heuristics, LLMs) without crashing a sub-game.
- **Barriers are Cop-only and Thief-only-blocking**: `can_place_barrier`
  restricts placement to `Role.COP` under `max_barriers`; `is_move_legal`
  only checks the barrier set for `Role.THIEF`, so the Cop can freely
  cross its own barriers.
- **Starting positions are caller-supplied**: `run_game_series` takes an
  explicit list of `(cop_start, thief_start)` pairs, one per sub-game,
  rather than generating them internally — placement strategy (random vs.
  fixed) is deliberately left to the orchestrator layer (a later stage),
  keeping this module a pure rules engine.

## Acceptance criteria (met)

- Movement respects grid bounds in all 4 directions.
- Thief is blocked by barriers; Cop is not.
- Cop placing a barrier consumes one of `max_barriers` and does not move it.
- Capture ends the sub-game immediately (mid-round, before the "other"
  player's turn if it was the mover who caused the coincidence).
- A sub-game with no capture after `max_moves` rounds is a Thief win.
- A full series accumulates the correct cop/thief totals across
  `num_games` sub-games per the config-driven scoring table.
- ≥85% test coverage (currently 100% on all Stage 1 modules), zero Ruff
  violations.
