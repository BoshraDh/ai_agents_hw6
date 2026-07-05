# Prompt Engineering Log

Per the submission guidelines, this documents the AI-assisted ("vibe
coding") development process for this project: what was asked of the AI
assistant at each stage, and — more importantly — what iterative
refinements happened when the first attempt wasn't right. This is a
summary of the actual development session, not a reconstruction.

## Stage 1 — Game engine

Prompted to implement the task doc's grid/turn/barrier/scoring rules as a
pure, I/O-free engine (`Position`, `Role`, `Action`, `Grid`, movement
legality, capture/survival checks, per-sub-game scoring, a 6-sub-game
series runner), config-driven via `config/setup.json`. Delivered directly
correct on the first pass; no bugs found during this stage's development.

## Stage 2 — MCP transport

Prompted to stand up two independent FastMCP servers (Cop, Thief) with a
stub `ping` tool, proving real HTTP transport. Required inspecting the
FastMCP library's actual API interactively (tool return-value shape,
`Client(mcp)` in-memory transport vs. `Client(url)` real HTTP, default
`/mcp` path) before writing code, rather than assuming the API shape.

## Stage 3 — Local orchestrator

Prompted to wire the Stage 1 engine to the Stage 2 servers end-to-end.
The core design challenge (identified and resolved through explicit
reasoning, not trial and error): the Stage 1 engine is synchronous but
FastMCP's `Client` is async-only. Solved with a dedicated
`AsyncBridge` (background event-loop thread) rather than making the
tested Stage 1 engine async — a deliberate design choice to avoid
touching already-correct, tested code.

## Stage 4 — Decision policies

Prompted for a "sophisticated strategy" beyond random movement. This
stage surfaced the most iteration of the project:

1. First heuristic (plain greedy distance minimization) was found, via
   direct testing, to fall into a stable non-capturing oscillation
   against an equally-greedy Thief — a real pursuit-evasion pathology,
   not a coding mistake. Fixed with 1-ply lookahead (Cop anticipates the
   Thief's flee response).
2. A barrier-placement heuristic was added, then found — again via
   direct testing, not first-principles review — to make the Cop
   barricade its own starting corner (since corners always have few
   open neighbors regardless of barriers, which never block the Cop).
   Removed rather than patched further.
3. Q-learning's training loop initially always started from the same
   fixed opposite corners, leaving close-range states poorly learned;
   found by testing capture behavior at short range after training, and
   fixed by randomizing starting positions every training episode.

All three fixes were verified empirically (re-running the affected
scenario) before moving on, not merely reasoned about abstractly.

## Stage 5 — Natural-language protocol

Prompted to replace the ground-truth opponent-position channel with real
LLM-driven communication via OpenAI, through a centralized rate-limited
gatekeeper. Design discussion up front established the key constraint:
the prompt builder must be structurally incapable of referencing the
opponent's position (enforced later by a signature-introspection test),
matching the Dec-POMDP partial-observability framing from the task doc.
Verified against the real OpenAI API (not just mocks): a real call
produced a legal action and a genuine free-text message; a real 3x3-grid
game with both sides LLM-driven completed correctly, with one honest
observation logged rather than smoothed over — the Thief's message
volunteered its exact position rather than being vague, since the prompt
permits deception without incentivizing it.

## Stage 6 — Visualization (optional)

Prompted for an optional CLI grid visualization without touching how the
game is decided or scored. Delivered as a purely additive, backward-
compatible `on_turn` callback on the engine (defaulting to `None`),
verified by re-running the full Stage 1-5 test suite unchanged afterward.

## Stage 8 — Gmail reporting

Prompted to reuse (not recreate) the Google OAuth client already set up
and validated earlier in this same session for an unrelated
calendar/draft test program. A real bug was found here specifically
through manual verification, not code review: sending the first real
report silently narrowed the *shared* token file's recorded scopes
(dropping `calendar.events`, needed by the other project) because the
credentials were loaded with an explicit, narrower scope override. Fixed
by loading the cached token without forcing a scopes argument; the fix
was confirmed by re-sending a second real email and re-inspecting the
shared token file's scopes afterward.

## Overall pattern

Across stages, the recurring theme was: **claims about behavior were
checked by actually running the code** (direct Python calls to the
engine, real HTTP calls to real MCP servers, one real OpenAI call, two
real Gmail sends) rather than assumed from reading the code. Three of the
four real bugs found in this project (Stage 4's oscillation, corner-pinch,
and training-coverage bugs, plus Stage 8's scope-narrowing bug) were only
discovered because of that verification discipline — none would have
been caught by unit tests alone, since the unit tests were written to
match the (buggy) behavior at the time.
