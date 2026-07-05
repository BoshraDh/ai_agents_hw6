# PRD — MCP Transport (Stage 2)

## Purpose

Prove that the Cop and Thief agents can each run behind their own
independent [FastMCP](https://github.com/jlowin/fastmcp) server — separate
processes, separate ports, no shared memory — before any game state, LLM
reasoning, or natural-language protocol is wired in. This is the transport
skeleton every later stage builds on.

## Design decisions

- **Two independent FastMCP apps**: `servers/cop_server/server.py` and
  `servers/thief_server/server.py`. Each module module-level-constructs its
  own `mcp: FastMCP` instance and exposes a `main()` process entry point —
  nothing is shared at runtime between the two other than identical code
  *shape* (both call the same factory).
- **No duplicated server-construction logic**: both servers are built via
  `servers/common.py::build_stub_server(name, ready_message)`, which
  registers a single stub `ping` tool. This keeps the two server modules to
  a ~15-line thin wrapper each (name + config + `mcp.run(...)`), per the
  submission guidelines' "no duplicated logic across 2+ files" rule.
- **HTTP transport, not stdio**: `mcp.run(transport="http", host=..., port=...)`.
  stdio is the default FastMCP transport for single-process CLI tools, but
  the task doc requires two servers reachable independently over the
  network (localhost now, cloud later) — HTTP is the only transport that
  satisfies that from Stage 2 onward.
- **Ports and hosts are config-driven**: `config/mcp_servers.json` (loaded
  via `shared/mcp_config.py::load_mcp_servers_config`) — no hard-coded
  host/port in the server modules themselves. Default: Cop on
  `127.0.0.1:8001`, Thief on `127.0.0.1:8002`.
- **Stub tool only**: the single `ping` tool returns a fixed "ready"
  string identifying which server answered. It exists purely to prove the
  transport round-trip; it carries no game logic. Real tools (state
  queries, move/message exchange) replace it in Stage 3 (wiring to the
  Stage 1 engine) and Stage 5 (LLM-backed natural-language exchange).

## Testing strategy

- **Unit tests** (`tests/unit/servers/`, `tests/unit/shared/test_mcp_config.py`)
  use FastMCP's in-memory `Client(mcp)` transport — no real sockets, no
  network flakiness — to verify each server is named correctly and its
  `ping` tool returns the expected message, plus that the two configured
  ports are distinct.
- **Integration test** (`tests/integration/test_mcp_transport.py`) starts
  *both* real server objects concurrently via `run_async(transport="http", ...)`
  on dedicated test ports (8091/8092, distinct from the production config
  ports so the test never collides with a real running instance), polls
  until each port accepts a TCP connection, then connects to each
  independently over real HTTP and calls `ping`. This is the closest
  automated proxy for "two independent localhost processes" without
  actually spawning OS subprocesses in the test suite.
- **Manual verification performed this stage**: both servers were also
  launched as real separate OS processes on the production config ports
  (`uv run python -m cop_thief_mcp.servers.cop_server.server` /
  `...thief_server.server`) and queried independently over HTTP — confirmed
  `cop-server-ready` / `thief-server-ready` from ports 8001/8002
  respectively, then the processes were stopped.

## Acceptance criteria (met)

- Two separately importable, separately runnable FastMCP server modules
  exist, sharing no runtime state.
- Both can be started concurrently and answer independently over HTTP on
  distinct, config-driven ports.
- 100% test coverage on all Stage 2 modules (entry-point `main()` functions
  are marked `# pragma: no cover` as thin process wrappers already exercised
  by the integration test's use of the same `mcp` objects); zero Ruff
  violations.
