# Cost & Token Analysis

## Which parts of this project cost money

- **`heuristic`, `random_walk`, `q_learning` decision policies**: **zero**
  external API cost. All computation is local Python (grid math / a small
  Q-table). This is the default (`config/setup.json`'s `decision_policy`).
- **`llm` decision policy**: one OpenAI API call per turn, per side.
- **Gmail reporting** (Stage 8): one Gmail API call per completed series
  (`users.messages.send`). Gmail's API has no per-request dollar cost for
  this usage pattern (it's quota-limited, not billed per call), so this
  section focuses on the OpenAI side.

## Model and observed usage

- Model: `gpt-4o-mini` (`services/llm/openai_agent.py::MODEL`).
- Real calls made during this session's Stage 5 verification (see
  `docs/PRD_mcp_orchestration.md` and `docs/PROMPT_ENGINEERING_LOG.md`):
  one standalone `decide_turn` call, plus a full small (3x3 grid, capped
  at 6 moves) real game with both sides LLM-driven, captured in 4 moves —
  so on the order of **7-8 real API calls total** were made in this
  project's entire development and verification history.
- Exact per-call token counts were not captured at call time (the OpenAI
  Python SDK's response object exposes a `usage.prompt_tokens` /
  `usage.completion_tokens` field that wasn't logged during those calls).
  The estimate below is derived from the actual prompt *text* sizes in
  `services/llm/prompts.py`, not a real API-reported count.

## Per-call estimate

- **System prompt** (`build_system_prompt`): fixed text, ~230 words ≈
  ~300 tokens (English text averages ~1.3 tokens/word).
- **User prompt** (`build_user_prompt`): own position, grid size,
  barriers, move counters, and the opponent's message — typically
  ~60-120 words ≈ ~80-160 tokens, growing slightly with barrier count and
  message length.
- **Response**: a small JSON object (`{"action": ..., "message": ...}`)
  — typically ~30-80 tokens depending on message length.
- **Estimated total per turn, per side**: roughly **400-550 tokens**
  (input-heavy, since the system prompt is fixed and re-sent every call
  rather than cached across turns).

## Estimated cost for a full series

Worst case: `config/setup.json` defaults to `max_moves: 25`, `num_games: 6`,
both sides on the `llm` policy — up to `25 * 2 * 6 = 300` calls in the
theoretical maximum (games typically end well before the move cap once
either side has a working chase strategy; the real verified game ended in
4 moves).

At ~470 tokens/call average (roughly 350 input + 120 output) and
`gpt-4o-mini`'s per-token pricing (**approximate** — confirm current
rates on OpenAI's pricing page before relying on this for budgeting):

| | Per call | Full 300-call worst case |
|---|---|---|
| Input tokens | ~350 | ~105,000 |
| Output tokens | ~120 | ~36,000 |
| Estimated cost | well under $0.001 | **under $0.05** total |

Even the theoretical worst case (every sub-game running the full 25-move
cap) costs a small fraction of a dollar with this model. The real
verified game (4 moves, one side only needed to call the model a few
times before capture) cost a small fraction of that worst case.

## Cost controls already in place

- `shared/gatekeeper.py::ApiGatekeeper` enforces `config/rate_limits.json`'s
  `services.openai.requests_per_minute` (default 30/minute) — bounds
  how fast calls can be made, independent of dollar cost, but also a
  practical brake on runaway usage (e.g. an infinite loop).
- `decision_policy` defaults to `"heuristic"` (free), not `"llm"` — the
  paid path is opt-in, never triggered by routine test runs or casual use.
- All automated tests mock the OpenAI client entirely — the test suite
  itself has never made a real, billed API call.

## Recommendation for future work

If this project needs precise cost tracking (e.g. for a longer research
run), the response object's `usage` field should be captured and logged
in `services/llm/openai_agent.py::decide_turn` rather than discarded —
this was not required for the stages actually built, so it was not added
speculatively.
