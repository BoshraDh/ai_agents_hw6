# PRD — Orchestrator & Full Local Run (Stage 3)

## Purpose

Wire the Stage 1 game engine and the Stage 2 MCP servers together into a
single, fully working local pipeline: a real 6-game series, played move by
move through genuine MCP tool calls over HTTP, with no LLM or NL protocol
yet (that's Stage 4/5). This stage proves *wiring*, not intelligence.

## The sync/async boundary problem

The Stage 1 engine (`run_sub_game`/`run_game_series`) is deliberately
synchronous and was left untouched — it calls `policy(context)` directly
in a plain `for` loop. FastMCP's `Client`, however, is async-only. Rather
than making the tested Stage 1 engine async (which would force every
existing Stage 1 test to change), Stage 3 introduces
`shared/async_bridge.py::AsyncBridge`: a background event-loop thread that
sync code can hand coroutines to and block for the result
(`bridge.run(coro)`). This is the standard "sync-calls-async" bridging
pattern and keeps Stage 1 exactly as it was.

## Components added this stage

- **`services/decision/random_walk.py`** — `choose_random_legal_action`:
  picks uniformly among legal movement actions, or `PASS` if boxed in.
  This is an intentionally dumb placeholder — it exists solely to prove
  the full request/response cycle end-to-end. Stage 4 replaces it with a
  real heuristic/Q-table policy behind the exact same tool interface.
- **`servers/common.py::build_agent_server`** — extended from Stage 2's
  stub-only factory to also expose a `decide_move` tool. Its request model
  (`TurnRequest`) intentionally carries only the acting agent's own
  position, the grid, and barriers — **never the opponent's position**.
  This enforces the Dec-POMDP partial-observability boundary from
  `docs/PRD_game_engine.md` at the transport level, from Stage 3 onward,
  not just once the NL layer (Stage 5) arrives.
- **`servers/lifecycle.py`** — `start_http_server`/`stop_server`/
  `wait_for_port`, extracted from Stage 2's integration test (which now
  imports them instead of duplicating them) so "run a server in the
  background and wait until reachable" exists in exactly one place, reused
  by both the transport test and the real orchestrator.
- **`orchestrator/mcp_policy.py`** — `build_mcp_policy(server_url, bridge)`
  returns a Stage-1-compatible `Policy` callable that, for each turn, calls
  the agent's own MCP server's `decide_move` tool (via the bridge) and
  parses the returned action name back into the engine's `Action` enum.
  `build_decide_move_request` (the context → wire-request conversion) is
  pure and separately unit-tested.
- **`orchestrator/local_runner.py`** — `run_full_local_series`: loads
  config, starts both real MCP servers via the bridge, builds an
  MCP-backed policy for each side, calls Stage 1's `run_game_series`
  unmodified, then tears everything down. This is the single function a
  CLI or test calls for "run the whole thing locally."

## Testing strategy

- Unit tests cover the placeholder policy (`random_walk`), the pure
  request-builder (`build_decide_move_request` — asserted to omit the
  opponent's position), the `AsyncBridge` in isolation, and the
  `decide_move`/`ping` tools via FastMCP's in-memory `Client`.
- The Stage 2 integration test was refactored to import the shared
  `servers/lifecycle.py` helpers instead of duplicating them.
- A new integration test (`tests/integration/test_local_full_run.py`) runs
  a complete 3-sub-game series (small 3x3 grid, low move cap for speed)
  through both real servers over real HTTP, using dedicated test ports and
  an explicitly constructed config so it never touches the production
  config or ports.
- **Manually verified this stage**: a full 6-game series was run against
  the actual production config (5x5 grid, ports 8001/8002) and produced a
  correct, non-trivial mix of Cop/Thief wins with accumulated totals.

## Acceptance criteria (met)

- A full local game series runs end-to-end through two real, independent
  MCP server processes, using only real HTTP tool calls for every move
  decision on both sides.
- No opponent position is ever transmitted over MCP.
- Stage 1's engine required zero changes.
- 99%+ coverage across all Stage 3 modules, zero Ruff violations, all
  files well under the 150-line cap.
