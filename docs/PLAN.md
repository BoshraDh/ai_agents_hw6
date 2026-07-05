# PLAN — Architecture & Roadmap

## Build order (matches the task doc's staged progression, Table 4)

| # | Stage | Status |
|---|-------|--------|
| 1 | Game logic, grid rules, movement, barriers, win conditions, scoring | **Done** |
| 2 | Basic MCP transport — two independent FastMCP servers (stub tools) | **Done** |
| 3 | Full local run: orchestrator drives real turns end-to-end on localhost | Not started |
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
│   │   ├── decision/        # heuristic.py, q_learning.py (stage 4)
│   │   └── reporting/       # gmail_report.py (stage 8)
│   ├── servers/
│   │   ├── common.py         # DONE — shared stub-server factory (no duplication between the two servers)
│   │   ├── cop_server/       # DONE — FastMCP app, stub `ping` tool, port from config
│   │   └── thief_server/     # DONE — FastMCP app, stub `ping` tool, port from config
│   ├── orchestrator/        # MCP-client game runner (stage 3+)
│   ├── shared/               # DONE — config.py, mcp_config.py, json_loader.py, version.py, constants.py; gatekeeper.py (stage 5+)
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

## Open design decisions deferred to later stages

- Exact prompt/message format for the NL exchange (Stage 5) — see
  `docs/PRD_mcp_orchestration.md` once written.
- Whether Q-learning is enabled by default or opt-in (Stage 4).
- Cloud provider specifics and auth token mechanism (Stage 7, deferred).
