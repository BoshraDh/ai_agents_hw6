# PLAN — Architecture & Roadmap

## Build order (matches the task doc's staged progression, Table 4)

| # | Stage | Status |
|---|-------|--------|
| 1 | Game logic, grid rules, movement, barriers, win conditions, scoring | **Done** |
| 2 | Basic MCP transport — two independent FastMCP servers (stub tools) | **Done** |
| 3 | Full local run: orchestrator drives real turns end-to-end on localhost | **Done** |
| 4 | Decision mechanism: heuristic first, Q-table as an optional pluggable policy | **Done** |
| 5 | Natural-language protocol: real LLM-generated messages replace stubs | **Done** |
| 6 | Optional GUI/CLI visualization of the grid | **Done** |
| 7 | Cloud deployment (e.g. Prefect Cloud), tokens, revocable auth | Deferred |
| 8 | Gmail API integration — auto-report JSON at end of 6-game series | Not started |

Only one stage is worked at a time; each stage's code + docs are committed
and pushed together, followed by an explicit checkpoint with the user
before starting the next stage.

## Architecture

```
cop-thief-mcp/
├── src/cop_thief_mcp/
│   ├── sdk/                 # single entry point for all business logic (added stage 3+)
│   ├── services/
│   │   ├── game/            # DONE — grid.py, rules.py, sub_game.py, game_series.py, scoring.py
│   │   ├── decision/        # DONE — random_walk.py, heuristic.py (default), q_learning.py + q_learning_training.py (optional), dispatch.py
│   │   └── reporting/       # gmail_report.py (stage 8)
│   ├── servers/
│   │   ├── common.py         # DONE — shared server factory: `ping` + `decide_move` tools
│   │   ├── lifecycle.py      # DONE — start/stop/wait_for_port, shared by tests + orchestrator
│   │   ├── cop_server/       # DONE — FastMCP app bound to Role.COP
│   │   └── thief_server/     # DONE — FastMCP app bound to Role.THIEF
│   ├── orchestrator/         # DONE — mcp_policy.py (+ message_exchange.py), local_runner.py
│   ├── services/llm/         # DONE — prompts.py, openai_agent.py, client_factory.py (Stage 5)
│   ├── services/visualization/ # DONE — grid_renderer.py (Stage 6, optional)
│   ├── cli/                  # DONE — watch_game.py (Stage 6, optional)
│   ├── shared/               # DONE — config.py, mcp_config.py, json_loader.py, async_bridge.py, gatekeeper.py, rate_limits_config.py, version.py, constants.py
│   └── main.py               # CLI entry point
├── tests/{unit,integration}/
├── docs/{PRD,PLAN,TODO}.md + PRD_<mechanism>.md per major mechanism
├── config/{setup.json, rate_limits.json, logging_config.json}
└── results/ notebooks/ assets/
```

## Stage 1 architecture notes (current)

- `services/game/grid.py` — `Position`, `Role`, `Action` and grid boundary
  checks. Pure geometry, no game rules.
- `services/game/rules.py` — move legality (barriers block the Thief only),
  barrier-placement eligibility, capture/survival checks.
- `services/game/scoring.py` — maps a sub-game outcome to (cop, thief)
  points via the config-driven `ScoringConfig`.
- `services/game/sub_game.py` — `run_sub_game` plays one sub-game via
  injected `Policy` callables (`TurnContext -> Action`), so the engine is
  agnostic to *how* a move is chosen. Scripted/deterministic test doubles
  stand in for real policies until Stage 4/5.
- `services/game/game_series.py` — `run_game_series` runs `num_games`
  sub-games back to back and accumulates cop/thief totals.
- `shared/config.py` — loads `config/setup.json` into a frozen
  `GameConfig`/`ScoringConfig`; this is the *only* place game parameters
  are read from — no hard-coded values anywhere else in the engine.

Starting positions per sub-game are intentionally left as a caller-supplied
parameter (`list[tuple[Position, Position]]`) rather than baked into the
engine — placement strategy (random draw vs. fixed layout) is an
orchestrator-level decision for a later stage, not a game-rule.

## Stage 2 architecture notes

- `servers/common.py::build_stub_server(name, ready_message)` — the only
  place a FastMCP app is constructed; both `cop_server` and `thief_server`
  call it with different arguments rather than duplicating setup code.
- `servers/cop_server/server.py` / `servers/thief_server/server.py` — thin
  (~15-line) process entry points: build the app via the shared factory,
  load their own host/port from config, run over HTTP transport.
- `shared/mcp_config.py` + `config/mcp_servers.json` — Cop/Thief host and
  port are config-driven, never hard-coded (defaults: `127.0.0.1:8001` /
  `127.0.0.1:8002`).
- `shared/json_loader.py` — extracted so `config.py` and `mcp_config.py`
  don't duplicate JSON-reading logic.
- Verified both servers run as genuinely independent processes (started
  separately via `uv run python -m cop_thief_mcp.servers.<name>.server`)
  and respond correctly on their own ports simultaneously — see
  `docs/PRD_mcp_transport.md` for full detail and testing strategy.

## Stage 3 architecture notes

- `services/decision/random_walk.py` — placeholder policy (uniformly
  random legal move, or PASS if boxed in). Proves wiring only; replaced
  behind the same `decide_move` tool interface in Stage 4.
- `servers/common.py::build_agent_server` now also registers a
  `decide_move` tool whose request (`TurnRequest`) carries the acting
  agent's own position, the grid, and barriers — **and, as of Stage 4,
  the opponent's position too** (see `docs/PRD_decision_engine.md` for
  why this reverses the "never the opponent's position" rule stated here
  originally).
- `shared/async_bridge.py::AsyncBridge` — a background event-loop thread
  so the still-synchronous Stage 1 engine can call FastMCP's async
  `Client` without becoming async itself.
- `orchestrator/mcp_policy.py` — builds a Stage-1-compatible `Policy`
  backed by a real `decide_move` MCP call; `build_decide_move_request`
  (the pure context → wire-request conversion) is separately unit-tested.
- `orchestrator/local_runner.py::run_full_local_series` — starts both real
  MCP servers, builds an MCP-backed policy per side, runs Stage 1's
  `run_game_series` unmodified, tears down. Manually verified against the
  production config: a full 6-game series produced a correct mix of
  Cop/Thief wins with accumulated totals.
- `servers/lifecycle.py` — extracted from Stage 2's integration test so
  "start/stop a background HTTP server and wait until reachable" exists
  once, reused by both the transport test and the orchestrator.

## Stage 4 architecture notes

- `services/decision/heuristic.py` — default policy. Cop uses 1-ply
  lookahead (anticipates the Thief's flee reply) to avoid a plain-greedy
  oscillation bug found during this stage; Thief flees greedily with a
  mobility tie-break. A barrier-placement heuristic was attempted, found
  buggy (see `docs/PRD_decision_engine.md`), and removed rather than
  patched further.
- `services/decision/q_learning.py` + `q_learning_training.py` — optional
  tabular Q-learning per the task doc's Bellman-equation recommendation,
  relative-position state encoding, self-play training with randomized
  starting positions (a training-coverage bug found and fixed this stage).
- `services/decision/dispatch.py` — single `choose_action(...)` selecting
  among `heuristic`/`random_walk`/`q_learning`; keeps decision logic out
  of the transport layer (`servers/common.py`).
- `config/setup.json` gained `decision_policy` (default `"heuristic"`).
- `servers/common.py::TurnRequest` gained `opponent_row`/`opponent_col`
  and `barriers_placed`/`max_barriers` — see the observability trade-off
  writeup in `docs/PRD_decision_engine.md`.
- Both the heuristic and Q-learning share a documented, understood
  limitation: starting exactly adjacent (distance 1) can produce a stable
  non-capturing cycle. Every other tested starting separation (distance
  >= 2, including opposite grid corners) captures reliably.

## Stage 5 architecture notes

- `services/llm/prompts.py` — pure system/user prompt builders. Structurally
  incapable of referencing the opponent's position (no such parameter
  exists in `build_user_prompt`'s signature, enforced by a test).
- `services/llm/openai_agent.py::decide_turn` — calls OpenAI via the
  gatekeeper, parses `{"action", "message"}` JSON, falls back to
  `random_walk` (empty message) on any failure (network, malformed JSON,
  illegal action).
- `services/llm/client_factory.py` — builds the OpenAI client from
  `OPENAI_API_KEY` only.
- `shared/gatekeeper.py` + `shared/rate_limits_config.py` +
  `config/rate_limits.json` — the mandatory centralized, rate-limited,
  retried chokepoint for every external API call (OpenAI now, Gmail in
  Stage 8).
- `orchestrator/message_exchange.py` + `mcp_policy.py::build_mcp_message_policy`
  — the NL analogue of Stage 4's ground-truth `build_mcp_policy`;
  `local_runner.py` picks between them based on `decision_policy`.
- `servers/common.py` — `TurnRequest` gained `opponent_message`/
  `moves_made`/`max_moves`; `decide_move` now always returns
  `TurnResponse{action, message}` (empty message for non-LLM policies).
- Full detail, the Dec-POMDP formalization, and testing strategy (mocked
  unit tests + a real-HTTP message-relay integration test) are in
  `docs/PRD_mcp_orchestration.md`.

## Stage 6 architecture notes (optional, per the task doc)

- `services/game/sub_game.py` — `run_sub_game` gained an optional
  `on_turn: OnTurn | None = None` parameter (threaded through
  `run_game_series` and `local_runner.py::run_full_local_series`),
  emitting a `TurnEvent` after every half-turn. Purely observational,
  backward compatible (defaults to `None`) — every Stage 1-5 test passed
  unchanged after this addition.
- `services/visualization/grid_renderer.py::render_grid` — pure ASCII
  rendering (`C`/`T`/`#`/`X`/`.`), no influence on gameplay.
- `cli/watch_game.py` — `uv run python -m cop_thief_mcp.cli.watch_game`
  prints the grid after every turn using whichever `decision_policy` is
  configured. Manually verified against the real local MCP pipeline.
- Live NL-message display alongside the grid was deliberately left out
  this stage (messages live in `MessageExchange`, not `TurnEvent`) — see
  `docs/PRD_visualization.md`.

## Open design decisions deferred to later stages

- Cloud provider specifics and auth token mechanism (Stage 7, deferred).
- Deeper (>1-ply) search or a non-adversarial evader model, to close the
  documented adjacent-distance capture gap (Stage 4), is left as future work.
- Whether `decision_policy` default switches from `"heuristic"` to `"llm"`
  once real end-to-end verification with an actual API key is complete.
- Whether the CLI visualizer should also display live NL messages
  alongside the grid (Stage 6 follow-up, not yet built).
