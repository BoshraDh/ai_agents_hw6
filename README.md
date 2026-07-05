# Cop vs Thief — Dual AI Agent Race via MCP Servers

Two independent AI agents — a **Cop** and a **Thief** — play a pursuit game
on a 2D grid across a 6-game series, communicating only through free
natural language over two separate [FastMCP](https://github.com/jlowin/fastmcp)
servers. See `docs/PRD.md` for the full requirements and `docs/PLAN.md` for
the staged build roadmap; this project is built one stage at a time.

**Current status: Stage 1 complete** — the pure game-logic engine (grid,
movement, barriers, win conditions, scoring) is implemented and tested. MCP
servers, LLM integration, and Gmail reporting land in later stages.

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

At Stage 1 this only loads and prints the game configuration; the full
pipeline (MCP servers + orchestrator + LLM agents) is wired up in later
stages per `docs/PLAN.md`.

## Configuration

All game parameters live in `config/setup.json` — grid size, max moves per
sub-game, number of sub-games in a series, max barriers, and the scoring
table. Nothing is hard-coded in source.

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
├── services/game/   # pure game-logic engine (Stage 1)
├── shared/           # config loading, version, constants
└── main.py           # CLI entry point
tests/unit/           # mirrors src/ structure
docs/                 # PRD.md, PLAN.md, TODO.md, PRD_<mechanism>.md
config/               # setup.json — all game parameters
```

## Documentation

- `docs/PRD.md` — product requirements
- `docs/PLAN.md` — architecture and staged roadmap
- `docs/TODO.md` — task tracking, stage by stage
- `docs/PRD_game_engine.md` — Stage 1 mechanism-specific design

## License

Course assignment submission (Dr. Yoram Segal) — not for redistribution.
