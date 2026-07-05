# PRD — MCP Orchestration & Natural-Language Protocol (Stage 5)

## Purpose

Replace the ground-truth opponent-position channel used by Stage 4's
heuristic/Q-table policies with genuine LLM-driven natural-language
communication between the Cop and Thief agents, via OpenAI, through a new
`llm` decision policy behind the same `decide_move` MCP tool. This is the
task document's central grading axis: the quality of the *communication*,
not who wins the game.

## Formal model (Dec-POMDP)

Per the task doc's formalism, `⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩`:

- **`n = 2`** agents: Cop and Thief.
- **`S`**: board state — both true positions, barrier set, moves made
  (unchanged from Stage 1).
- **`{Aᵢ}`**: `{UP, DOWN, LEFT, RIGHT, PASS, PLACE_BARRIER}` (movement
  actions only for the Thief) — unchanged from Stage 1.
- **`P`**: deterministic transition function — Stage 1's `rules.py`/
  `sub_game.py`, untouched by this stage.
- **`R`**: the config-driven scoring table — unchanged.
- **`{Ωᵢ}` and `O` (the interesting part this stage)**: each agent's
  observation is `(own_true_state, opponent_free_text_message)`. Crucially,
  **`O` is not a function of the true state alone** — the opponent's
  "observation" of you is mediated entirely by *your own LLM's choice of
  what to say*. This makes it a Dec-POMDP with a cheap-talk communication
  channel rather than a fixed noisy-sensor model: an agent can be
  truthful, vague, or actively deceptive, and the task doc explicitly
  calls out "coping with attempts at deception" as part of the exercise.
- **`γ`**: not directly exercised this stage (no RL training over the NL
  channel), but present in the formalism for completeness.

## What changed in the wire protocol

`servers/common.py::TurnRequest` gained `opponent_message: str = ""`,
`moves_made`, and `max_moves`; `opponent_row`/`opponent_col` became
optional (kept for the Stage 4 policies, **never read by the `llm` path**).
`decide_move` now always returns a `TurnResponse{action, message}` instead
of a bare action string — every policy (including Stage 4's) now emits a
message field, empty for non-LLM policies.

The **orchestrator** (`orchestrator/message_exchange.py` +
`orchestrator/mcp_policy.py::build_mcp_message_policy`) maintains a small
shared `MessageExchange(cop_message, thief_message)`: after each side's
`decide_move` call, its returned message is stored for the *other* side to
read on its next turn. `local_runner.py` selects between the ground-truth
policy builder (Stage 4) and the message-based one purely based on
`config/setup.json`'s `decision_policy` — no other code changed.

## The LLM agent (`services/llm/`)

- **`prompts.py`**: pure functions building the system/user prompts.
  `build_user_prompt` structurally has no `opponent_row`/`opponent_col`
  parameters at all (enforced by a signature-introspection test) — the
  *only* information about the opponent it can ever receive is the
  free-text message string.
- **`openai_agent.py::decide_turn`**: calls the model via
  `client.chat.completions.create(..., response_format={"type": "json_object"})`,
  expecting `{"action": ..., "message": ...}`. On *any* failure — network
  error, malformed JSON, or a syntactically valid but illegal action (out
  of bounds, barrier-blocked, a Thief trying to place a barrier) — it
  falls back to `random_walk`'s uniformly-random legal move with an empty
  message. The game must never break because of an LLM hiccup.
- **`client_factory.py`**: builds the OpenAI client from the
  `OPENAI_API_KEY` environment variable only; raises clearly if unset.
  Never hard-coded, never read from anywhere else.

## API Gatekeeper (`shared/gatekeeper.py`)

Per the submission guidelines, every external API call must go through a
centralized chokepoint. `ApiGatekeeper.execute(...)` wraps the OpenAI call:
enforces a config-driven requests-per-minute cap (sliding window),
retries transient failures up to a config-driven max, and logs every
attempt. Limits live in `config/rate_limits.json`
(`services.openai.{requests_per_minute,max_retries,retry_after_seconds}`),
never hard-coded in `openai_agent.py` itself.

## Testing strategy

- All automated tests mock the OpenAI client (`unittest.mock.MagicMock`)
  — **zero real API calls or cost in the test suite**. This covers prompt
  construction, response parsing, the legal/illegal-action fallback, and
  the gatekeeper's rate-limiting/retry logic in complete isolation.
- `tests/integration/test_llm_message_relay.py` proves the *transport* is
  real: two `llm`-policy MCP servers (mocked OpenAI clients, real HTTP)
  play one full turn, and the test asserts the Thief's message literally
  shows up inside the string sent to the Cop's (mocked) LLM call on its
  next turn, and vice versa — the message relay genuinely round-trips
  through MCP, not just through a shared Python object.
- **Real end-to-end verification** (an actual OpenAI API call) is done
  manually once a real `OPENAI_API_KEY` is available, matching how every
  prior stage's "does it actually work" claim was manually verified
  against real infrastructure, not just unit tests.

## Open item

`config/setup.json`'s `decision_policy` default remains `"heuristic"` as
of this stage — `"llm"` is fully implemented and tested but not yet the
default, pending a real API key for manual confirmation. See `docs/TODO.md`.

## Acceptance criteria

- `llm` is a fully working, config-selectable `decide_move` policy.
- The opponent's true position is never transmitted, read, or used
  anywhere in the `llm` code path (enforced by a structural test on
  `build_user_prompt`'s signature).
- A malformed/failed LLM call never crashes a game — always falls back
  to a legal move.
- All external OpenAI calls go through the rate-limited, retried
  `ApiGatekeeper` — none bypass it.
- Message relay is proven over real MCP HTTP transport, not just unit
  tests of individual functions.
