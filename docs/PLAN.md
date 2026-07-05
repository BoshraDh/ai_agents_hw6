# PLAN — Architecture & Roadmap

## Build order (matches the task doc's staged progression, Table 4)

| # | Stage | Status |
|---|-------|--------|
| 1 | Game logic, grid rules, movement, barriers, win conditions, scoring | **Done** |
| 2 | Basic MCP transport — two independent FastMCP servers (stub tools) | Not started |
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
│   │   ├── cop_server/      # FastMCP app (stage 2+)
│   │   └── thief_server/    # FastMCP app (stage 2+)
│   ├── orchestrator/        # MCP-client game runner (stage 3+)
│   ├── shared/               # DONE — config.py, version.py, constants.py; gatekeeper.py (stage 2+)
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

## Open design decisions deferred to later stages

- Exact prompt/message format for the NL exchange (Stage 5) — see
  `docs/PRD_mcp_orchestration.md` once written.
- Whether Q-learning is enabled by default or opt-in (Stage 4).
- Cloud provider specifics and auth token mechanism (Stage 7, deferred).
