# PLAN — Architecture & Roadmap

## Build order (matches the task doc's staged progression, Table 4)

| # | Stage | Status |
|---|-------|--------|
| 1 | Game logic, grid rules, movement, barriers, win conditions, scoring | **Done** |
| 2 | Basic MCP transport — two independent FastMCP servers (stub tools) | **Done** |
| 3 | Full local run: orchestrator drives real turns end-to-end on localhost | **Done** |
| 4 | Decision mechanism: heuristic first, Q-table as an optional pluggable policy | Not started |
| 5 | Natural-language protocol: real LLM-generated messages replace stubs | Not started |
| 6 | Optional GUI/CLI visualization of the grid | Not started |
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
│   │   ├── decision/        # DONE (placeholder) — random_walk.py; heuristic.py, q_learning.py (stage 4)
│   │   └── reporting/       # gmail_report.py (stage 8)
│   ├── servers/
│   │   ├── common.py         # DONE — shared server factory: `ping` + `decide_move` tools
│   │   ├── lifecycle.py      # DONE — start/stop/wait_for_port, shared by tests + orchestrator
│   │   ├── cop_server/       # DONE — FastMCP app bound to Role.COP
│   │   └── thief_server/     # DONE — FastMCP app bound to Role.THIEF
│   ├── orchestrator/         # DONE — mcp_policy.py, local_runner.py (full local run)
│   ├── shared/               # DONE — config.py, mcp_config.py, json_loader.py, async_bridge.py, version.py, constants.py; gatekeeper.py (stage 5+)
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
  `decide_move` tool whose request (`TurnRequest`) carries only the
  acting agent's own position, the grid, and barriers — never the
  opponent's position, enforcing partial observability at the transport
  level from this stage onward.
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

## Open design decisions deferred to later stages

- Exact prompt/message format for the NL exchange (Stage 5) — see
  `docs/PRD_mcp_orchestration.md` once written.
- Whether Q-learning is enabled by default or opt-in (Stage 4).
- Cloud provider specifics and auth token mechanism (Stage 7, deferred).
