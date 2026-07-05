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

## Stage 2 — Basic MCP transport

- [x] Add `fastmcp` dependency
- [x] `servers/common.py` — shared stub-server factory (no duplicated logic)
- [x] `servers/cop_server/` — minimal FastMCP app with a stub tool
- [x] `servers/thief_server/` — minimal FastMCP app with a stub tool
- [x] `config/mcp_servers.json` + `shared/mcp_config.py` — host/port config-driven
- [x] `shared/json_loader.py` — shared JSON reader (no duplication with `config.py`)
- [x] Prove both servers run independently on separate localhost ports (real
      OS processes on ports 8001/8002, manually verified)
- [x] Unit tests (in-memory `Client`) + integration test (real HTTP, two
      concurrent servers on dedicated test ports 8091/8092)
- [x] 100% coverage maintained (43 tests total), zero Ruff violations
- [x] `docs/PRD_mcp_transport.md` written; PRD/PLAN/TODO/README updated
- [x] Commit + push Stage 2
- [ ] Report to user, get go-ahead for Stage 3

## Stage 3 — Full local run

- [x] `services/decision/random_walk.py` — placeholder random-legal-move policy
- [x] `servers/common.py` — added `decide_move` tool (own state only, no opponent leak)
- [x] `servers/lifecycle.py` — start/stop/wait_for_port, extracted for reuse
- [x] `shared/async_bridge.py` — background event loop so sync engine can call async MCP client
- [x] `orchestrator/mcp_policy.py` — MCP-backed Policy + pure request builder
- [x] `orchestrator/local_runner.py` — `run_full_local_series`, wired to Stage 1 engine
- [x] Refactored Stage 2 integration test to reuse `servers/lifecycle.py`
- [x] Integration test: full local run on localhost, both servers + orchestrator
- [x] Manual run against production config: full 6-game series, real mixed outcomes
- [x] 57 tests total, 99.65% coverage, zero Ruff violations
- [x] `docs/PRD_orchestrator.md` written; PRD/PLAN/TODO/README updated
- [x] Commit + push Stage 3
- [ ] Report to user, get go-ahead for Stage 4

## Stage 4 — Decision mechanism

- [x] `services/decision/heuristic.py` — default policy: 1-ply-lookahead
      chase (Cop) / greedy flee with mobility tie-break (Thief)
- [x] Found + fixed: plain-greedy Cop oscillation bug (never captures from
      some starts without lookahead)
- [x] Found + removed: corner-pinch barrier heuristic (barricaded its own
      starting corner instead of chasing)
- [x] `services/decision/q_learning.py` + `q_learning_training.py` —
      optional tabular Q-table, Bellman-equation updates, self-play training
- [x] Found + fixed: training always started from the same fixed corners,
      leaving close-range states poorly learned; randomized per episode
- [x] `services/decision/dispatch.py` — config-selectable policy dispatch
- [x] `config/setup.json` — added `decision_policy` (default `heuristic`)
- [x] `servers/common.py` — `TurnRequest` extended with opponent position
      + barrier counts (documented reversal of Stage 3's no-opponent rule)
- [x] Documented known limitation: adjacent (distance-1) starts can still
      produce a non-capturing cycle for both policies; all other tested
      separations capture reliably
- [x] 83 tests total, 99.09% coverage, zero Ruff violations
- [x] `docs/PRD_decision_engine.md` written; PRD/PLAN/TODO/README updated
- [x] Commit + push Stage 4
- [x] Report to user, get go-ahead for Stage 5

## Stage 5 — Natural-language protocol

- [x] `shared/gatekeeper.py` + `shared/rate_limits_config.py` +
      `config/rate_limits.json` — centralized rate-limited OpenAI wrapper
- [x] `services/llm/prompts.py` — system/user prompt builders (no opponent
      position parameter, structurally guarded by a test)
- [x] `services/llm/openai_agent.py` — `decide_turn`, JSON parsing, legal-
      action validation, fallback to `random_walk` on any failure
- [x] `services/llm/client_factory.py` — OpenAI client from `OPENAI_API_KEY`
- [x] `servers/common.py` — `TurnRequest`/`TurnResponse` extended for the
      `llm` policy; `decide_move` always returns `{action, message}`
- [x] `orchestrator/message_exchange.py` + `mcp_policy.py::build_mcp_message_policy`
      — free-text message relay between the two sides
- [x] `local_runner.py` — selects ground-truth vs. message-based policy
      building per `decision_policy`
- [x] Unit tests fully mocked (zero real API calls/cost); integration test
      proves message relay over real MCP HTTP transport
- [x] 110 tests total, 98.82% coverage, zero Ruff violations, all files <= 137 lines
- [x] `docs/PRD_mcp_orchestration.md` — Dec-POMDP formalization + design
- [x] Real end-to-end verification with an actual `OPENAI_API_KEY`: single
      real `decide_turn` call, then a full real game (3x3 grid, real MCP
      servers, real OpenAI both sides, no mocking) -- Cop captured Thief
      in 4 moves, scored 20/5 correctly. See docs/PRD_mcp_orchestration.md.
- [x] Commit + push Stage 5
- [x] Report to user, get go-ahead for Stage 6

## Stage 6 — Optional visualization

- [x] `services/game/sub_game.py` — optional `on_turn`/`TurnEvent` callback,
      backward-compatible (threaded through `run_game_series` + `local_runner.py`)
- [x] `services/visualization/grid_renderer.py` — pure ASCII grid renderer
- [x] `cli/watch_game.py` — `uv run python -m cop_thief_mcp.cli.watch_game`
- [x] Unit tests for turn events, renderer, and CLI printer (all via `capsys`)
- [x] Manually ran the CLI watch script against the real local MCP
      pipeline; grid updates correctly turn by turn
- [x] All prior Stage 1-5 tests pass unchanged (no behavior change)
- [x] 119 tests total, 98.92% coverage, zero Ruff violations
- [x] `docs/PRD_visualization.md` written; PRD/PLAN/TODO/README updated
- [x] Commit + push Stage 6
- [ ] Report to user, get go-ahead for Stage 7/8

## Stage 7 — Cloud deployment (deferred, not started)

- [ ] Prefect Cloud (or alternative) deployment of both MCP servers
- [ ] Token-based auth, revocable

## Stage 8 — Gmail reporting (not started)

- [ ] `services/reporting/gmail_report.py` — builds Internal Game JSON, sends via Gmail API
- [ ] Reuse OAuth pattern from `gmail-calendar-test`, secret path via env var
- [ ] Wire into end of 6-game series in the orchestrator
