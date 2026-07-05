# Cop vs Thief — Dual AI Agent Race via MCP Servers

Two independent AI agents — a **Cop** and a **Thief** — play a pursuit game
on a 2D grid across a 6-game series, communicating only through free
natural language over two separate [FastMCP](https://github.com/jlowin/fastmcp)
servers. See `docs/PRD.md` for the full requirements and `docs/PLAN.md` for
the staged build roadmap; this project is built one stage at a time.

**Current status: Stage 4 complete** — the game engine, the two independent
MCP servers, the local orchestrator, and a real decision mechanism (a
default chase/flee heuristic, plus an optional tabular Q-learning policy)
are all wired together. Move selection is genuinely tactical, config-selectable
via `decision_policy` in `config/setup.json` — see `docs/PRD_decision_engine.md`
for the design, a couple of real bugs found and fixed along the way, and an
honestly documented known limitation. The natural-language protocol (Stage 5)
and Gmail reporting (Stage 8) land in later stages.

## Requirements

- Python >= 3.12
- [`uv`](https://docs.astral.sh/uv/) for all dependency/environment management
  (no bare `pip`/`venv`)

## Installation

```bash
uv sync
```

## Usage

```bash
uv run python -m cop_thief_mcp.main
```

At this stage `main.py` only loads and prints the game configuration; the
full pipeline (orchestrator + LLM agents) is wired up in later stages per
`docs/PLAN.md`.

## Running the MCP servers (Stage 2)

Each agent's FastMCP server is an independent process:

```bash
uv run python -m cop_thief_mcp.servers.cop_server.server    # http://127.0.0.1:8001/mcp
uv run python -m cop_thief_mcp.servers.thief_server.server  # http://127.0.0.1:8002/mcp
```

Each exposes a `ping` health-check and a `decide_move` tool, backed by the
policy named in `config/setup.json`'s `decision_policy`
(`"heuristic"` [default], `"random_walk"`, or `"q_learning"`) — see
`docs/PRD_decision_engine.md`. Host/port come from `config/mcp_servers.json`.

## Running a full local game series

```bash
uv run python -c "
from cop_thief_mcp.orchestrator.local_runner import run_full_local_series
from cop_thief_mcp.services.game.grid import Position

starts = [(Position(0, 0), Position(4, 4)) for _ in range(6)]
result = run_full_local_series(starts)
print(result.cop_total, result.thief_total)
"
```

This starts both MCP servers, plays a real 6-game series entirely through
MCP tool calls, and tears the servers down afterward.

## Configuration

All game parameters live in `config/setup.json` — grid size, max moves per
sub-game, number of sub-games in a series, max barriers, the decision
policy, and the scoring table. Nothing is hard-coded in source.

## Testing

```bash
uv run pytest tests/ --cov=src --cov-report=term-missing
uv run ruff check .
```

Coverage must stay at or above 85% (currently 100% on all implemented
modules); linting must pass with zero violations.

## Project structure

```
src/cop_thief_mcp/
├── services/game/         # pure game-logic engine (Stage 1)
├── services/decision/      # decision policies behind the decide_move tool (Stage 3+)
├── servers/                # Cop/Thief FastMCP servers (Stage 2-3)
├── orchestrator/           # MCP-client game runner, full local run (Stage 3)
├── shared/                 # config loading, version, constants, async bridge
└── main.py                 # CLI entry point
tests/unit/                # mirrors src/ structure
tests/integration/          # cross-component tests (real MCP transport + full local run)
docs/                       # PRD.md, PLAN.md, TODO.md, PRD_<mechanism>.md
config/                     # setup.json, mcp_servers.json — all parameters
```

## Documentation

- `docs/PRD.md` — product requirements
- `docs/PLAN.md` — architecture and staged roadmap
- `docs/TODO.md` — task tracking, stage by stage
- `docs/PRD_game_engine.md` — Stage 1 mechanism-specific design
- `docs/PRD_mcp_transport.md` — Stage 2 mechanism-specific design
- `docs/PRD_orchestrator.md` — Stage 3 mechanism-specific design
- `docs/PRD_decision_engine.md` — Stage 4 mechanism-specific design

## License

Course assignment submission (Dr. Yoram Segal) — not for redistribution.
