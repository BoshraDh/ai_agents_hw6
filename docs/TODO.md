# TODO

## Stage 1 — Game logic, grid rules, movement, barriers, win conditions, scoring

- [x] Clone repo, scaffold uv project (`src/` layout, `pyproject.toml`, `.gitignore`, `.env-example`)
- [x] `services/game/grid.py` — Position, Role, Action, Grid boundary checks
- [x] `services/game/rules.py` — move legality, barrier eligibility, capture/survival
- [x] `services/game/scoring.py` — outcome -> (cop, thief) points from config
- [x] `services/game/sub_game.py` — turn loop (Thief-first, alternating, max_moves cap)
- [x] `services/game/game_series.py` — 6 sub-games, accumulated totals
- [x] `shared/config.py` + `config/setup.json` — config-driven parameters, no hard-coding
- [x] `shared/version.py` — version starts at 1.00
- [x] Unit tests for every module (34 tests, 100% coverage, `fail_under = 85` enforced)
- [x] `uv run ruff check .` — zero violations
- [x] `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md`, `docs/PRD_game_engine.md` written
- [x] Commit + push Stage 1
- [ ] Report to user, get go-ahead for Stage 2

## Stage 2 — Basic MCP transport (not started)

- [ ] Add `fastmcp` dependency
- [ ] `servers/cop_server/` — minimal FastMCP app with a stub tool
- [ ] `servers/thief_server/` — minimal FastMCP app with a stub tool
- [ ] Prove both servers run independently on separate localhost ports
- [ ] Unit/integration tests for server startup and stub tool calls
- [ ] Update PRD/PLAN/TODO, commit + push

## Stage 3 — Full local run (not started)

- [ ] `orchestrator/` — MCP-client game runner driving real turns end-to-end
- [ ] Wire orchestrator to the Stage 1 game engine (apply real moves from tool calls)
- [ ] Integration test: full local run on localhost, both servers + orchestrator

## Stage 4 — Decision mechanism (not started)

- [ ] `services/decision/heuristic.py` — default policy (e.g. distance-based)
- [ ] `services/decision/q_learning.py` — optional tabular Q-table policy

## Stage 5 — Natural-language protocol (not started)

- [ ] `docs/PRD_mcp_orchestration.md` — Dec-POMDP formalization, NL protocol design
- [ ] `shared/gatekeeper.py` — centralized rate-limited OpenAI client wrapper
- [ ] Replace stub messages with real LLM-generated NL messages

## Stage 6 — Optional visualization (not started)

- [ ] Minimal CLI/GUI rendering of the grid per turn

## Stage 7 — Cloud deployment (deferred, not started)

- [ ] Prefect Cloud (or alternative) deployment of both MCP servers
- [ ] Token-based auth, revocable

## Stage 8 — Gmail reporting (not started)

- [ ] `services/reporting/gmail_report.py` — builds Internal Game JSON, sends via Gmail API
- [ ] Reuse OAuth pattern from `gmail-calendar-test`, secret path via env var
- [ ] Wire into end of 6-game series in the orchestrator
