# PRD — Cop vs Thief: Dual AI Agent Race via MCP Servers

## Overview

Two independent AI agents — a **Cop** and a **Thief** — play a pursuit game on a
2D grid across a series of 6 sub-games. Each agent runs behind its own
[FastMCP](https://github.com/jlowin/fastmcp) server and the two agents
communicate **only through free natural language** (no shared memory, no
rigid message schema). The graded outcome is the quality of the MCP
orchestration and inter-agent communication — not which side wins the game.

Source requirements: `ex06-Dual AI agent race via MCP servers.pdf` (Dr. Yoram
Segal), cross-checked against `software_submission_guidelines-V3.pdf` for
project scaffold/quality requirements.

## Goals

- A fully working local pipeline: two MCP servers (Cop, Thief) + an
  orchestrator that runs a complete 6-game series end to end.
- Game mechanics that exactly match the task document's rules (grid,
  turn order, barriers, win conditions, scoring).
- An automated JSON summary report emailed via the Gmail API when the
  6-game series completes.
- Full compliance with the submission guidelines (SDK architecture, API
  gatekeeper, ≥85% test coverage, uv-only tooling, docs, no hard-coding).

## Scope decisions (locked in with the user)

- **Solo submission.** No inter-group bonus game / cross-team JSON schema.
- **LLM provider: OpenAI**, called directly (architecture 7.1 in the task doc
  — the simplest/recommended option), via the central API gatekeeper.
- **Cloud deployment (e.g. Prefect Cloud) is deferred.** The local
  (`localhost`, two ports) pipeline must be fully proven first; cloud comes
  in a later stage, not part of the current build.
- Reuses the Gmail OAuth pattern already validated in this environment
  (`google-auth` / `google-auth-oauthlib` / `google-api-python-client`,
  token cached next to the OAuth client-secret file) — the secret/token path
  is read from an environment variable, never hard-coded.

## Game rules (source of truth: task doc section 4)

- **Board**: dynamic grid, size from config (default `5x5`).
- **Sub-game**: capped at `max_moves` (default 25). Turn order: **Thief
  moves first, then Cop**, alternating. Each turn a player moves one cell
  (4 directions) or passes.
- **Game**: a series of `num_games` sub-games (default 6); scores accumulate.
- **Win conditions**: Cop wins by landing on the Thief's cell (capture).
  Thief wins by surviving the full sub-game without being caught.
- **Barriers**: instead of moving, the Cop may place a barrier on its
  current cell (max `max_barriers` per sub-game, default 5). A barrier
  blocks the Thief only — the Cop can still cross it. Only the Cop may
  place barriers.
- **Scoring per sub-game**: Cop win → Cop 20 / Thief 5. Thief win → Thief
  10 / Cop 5. All figures are config-driven, not hard-coded.
- **Progressive sanity checks**: the pipeline must be provably correct at
  increasing grid sizes — 2x2 → 3x3/3x2 → 4x4/4x3 → 5x5 — each a checkpoint
  before scaling up (task doc section 4.5, table 2).

## Partial observability (Dec-POMDP framing)

Each agent knows the grid, barrier layout, its own position, and its
moves/barriers remaining — but is **never given the opponent's exact
coordinates programmatically**. The only channel for inferring the
opponent's location is the free-text natural-language message the
opponent's LLM chooses to send each turn. This is what makes the NL
channel load-bearing rather than decorative, and matches the task doc's
Dec-POMDP formalization (`⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩`) — full detail in
`docs/PRD_mcp_orchestration.md`.

## Non-goals (current stage)

Stages 1–5 (complete) cover the pure game-logic engine, the MCP transport
skeleton, a fully wired local orchestrator, a real decision mechanism
(heuristic/Q-learning), and now genuine LLM-driven natural-language
communication (the `llm` decision policy, OpenAI-backed) — see
`docs/PRD_mcp_orchestration.md` for the Dec-POMDP formalization and design,
and `docs/PRD_decision_engine.md` for Stage 4's documented limitations.
Real end-to-end verification of the `llm` policy against the actual OpenAI
API is still pending a live API key (unit/integration tests are fully
mocked). GUI, cloud deployment, and Gmail reporting remain out of scope
until their respective stages (see `docs/PLAN.md`).

## Success criteria

- `uv run pytest tests/ --cov=src` passes with ≥85% coverage (currently 100%).
- `uv run ruff check .` passes with zero violations.
- Each stage in `docs/PLAN.md` is completed, documented, committed, and
  pushed before the next stage begins.
