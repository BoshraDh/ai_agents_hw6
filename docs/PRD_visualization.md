# PRD — Grid Visualization (Stage 6, optional)

## Purpose

An optional CLI visualization of the grid per turn, per the task doc's
Table 4 — explicitly optional, since the graded deliverable is MCP
orchestration quality, not presentation. Kept proportionately small: a
pure ASCII renderer plus a thin CLI script, with no changes to how the
game is decided or scored.

## Design

- **`services/game/sub_game.py`**: gained an optional `on_turn: OnTurn | None = None`
  parameter on `run_sub_game` (and threaded through `run_game_series` and
  `orchestrator/local_runner.py::run_full_local_series`). Called once per
  half-turn (Thief's move, then Cop's) with a `TurnEvent` (move number,
  role, action, both positions, barriers, whether this move captured).
  **Backward compatible**: defaults to `None`, so every existing caller
  and test needed zero changes — verified by running the full Stage 1-5
  test suite unchanged after this addition.
- **`services/visualization/grid_renderer.py::render_grid`**: a pure
  function, board state in, ASCII string out (`C`/`T`/`#`/`X`/`.` for
  Cop/Thief/barrier/capture/empty). Has no dependency on, or influence
  over, gameplay — it only ever reads state the engine already computed.
- **`cli/watch_game.py`**: `uv run python -m cop_thief_mcp.cli.watch_game`
  runs a full local series (whichever `decision_policy` is configured)
  and prints the grid after every half-turn via `build_console_printer`,
  which wraps `render_grid` as an `on_turn` callback.

## Why not thread NL messages into the same view

The `llm` policy's messages live in `orchestrator/message_exchange.py`'s
`MessageExchange`, not in `TurnEvent` — the engine has no concept of
messages at all (by design, see `docs/PRD_mcp_orchestration.md`). Wiring
live message display into the same console view is a natural follow-up
but was left out of this stage to keep the addition minimal; the grid
view alone already satisfies "CLI visualization of the grid per turn."

## Verification

- Unit tests: `TurnEvent` emission/ordering/early-stop-on-capture
  (`test_sub_game_turn_events.py`), `render_grid` output for empty
  cells/barriers/capture/grid-shape (`test_grid_renderer.py`), and the
  CLI printer's stdout via `capsys` (`test_watch_game.py`).
- Manually ran `uv run python -m cop_thief_mcp.cli.watch_game` against
  the real local MCP pipeline (heuristic policy) and confirmed the grid
  updates correctly turn by turn, matching the Cop's actual chase.

## Acceptance criteria (met)

- Adding visualization required zero changes to scoring, rules, or any
  decision policy — purely observational.
- All prior tests (Stages 1-5) pass unchanged.
- The renderer and CLI printer are pure/testable without needing a real
  running game.
