# PRD — Gmail Auto-Report (Stage 8)

## Purpose

Per the task doc (section 9): once the Cop agent's 6-game series completes,
it must automatically send a single email containing a structured JSON
summary — the "Internal Game JSON" — to a fixed recipient, with the email
body containing **only** the JSON, no free text.

## Recipient and format

- Recipient: `rmisegal+uoh26b@gmail.com` (the address specified in the task
  doc), config-driven via `config/setup.json`'s `report_recipient` —
  overridable, never hard-coded in source.
- Body: exactly the JSON report, `json.dumps(report, indent=2)`, nothing
  else — verified by a test that splits the MIME body from the headers and
  asserts it parses as the report dict with no surrounding text.
- Schema (`services/reporting/game_report.py::build_game_report`):
  `group_name`, `students` (empty — solo submission), `github_repo`,
  `cop_mcp_url`/`thief_mcp_url` (from `config/mcp_servers.json`), `timezone`
  (`"Asia/Jerusalem"`), `sub_games` (outcome/moves/scores per sub-game),
  and `totals` — matching the task doc's example schema.

## Reusing the existing Google OAuth client

This project's Gmail access reuses the OAuth client (`client_google.json`)
and cached token already set up and validated earlier in this environment
for a separate calendar/draft test program — not a new client. The token
already carries `gmail.compose` scope, which per Google's own scope
documentation covers both draft management **and actually sending
messages**, so no new consent screen was needed.

- `services/reporting/gmail_client.py::build_gmail_service` — loads
  `GOOGLE_CLIENT_SECRET_PATH` from the environment, caches/refreshes the
  token alongside the client secret file.
- `services/reporting/gmail_sender.py::send_game_report` — builds the
  MIME message and sends via `users().messages().send(...)`, through the
  centralized `ApiGatekeeper` (a new `"gmail"` entry in
  `config/rate_limits.json`).
- `services/reporting/report_flow.py::send_series_report` — ties the
  report builder, Gmail client, and gatekeeper together into one call.

### A real bug found and fixed here: narrowing a *shared* token's scopes

`token.json` is shared with another of the user's projects (which also
needs `calendar.events`). The first implementation called
`Credentials.from_authorized_user_file(token_path, SCOPES)` with this
project's narrower `["gmail.compose"]` list. On token refresh, the
credentials object — now carrying only the *requested* scope, not the
file's original broader one — got serialized straight back over the
shared file, silently dropping `calendar.events` for the other project.
Caught by manually inspecting `token.json` after the first real send.
Fixed by loading the cached token **without** forcing a scopes argument
(`Credentials.from_authorized_user_file(token_path)`, no override) so
whatever is already recorded in the file is preserved; `SCOPES` is now
only used for a brand-new consent flow. The file's scopes were restored
and a second real send confirmed both scopes remained intact afterward.

## Trigger point

`orchestrator/local_runner.py::run_full_local_series` gained a
`send_report: bool = False` parameter. When `True` (only the "real" entry
point, `cli/run_series.py`, sets this), the report is built and sent once
`run_game_series` returns — after the MCP servers are already torn down,
since sending an email needs no live game server. Defaults to `False` so
every test and casual run never triggers a real email.

## Testing strategy

- All automated tests mock the Gmail API client and the OAuth flow
  entirely (`unittest.mock`) — **zero real emails sent by the test
  suite**. Covers: credential loading (missing env var, cached-valid
  path, no-token-file path), email-body construction (JSON-only body),
  and the send call's arguments/return value.
- `tests/integration/test_local_runner_report.py` proves the
  `send_report` flag is correctly wired into `run_full_local_series`
  (mocks `send_series_report` itself) — both the "triggers" and
  "defaults to off" cases.
- **Real end-to-end verification**: ran a real local game series with
  `send_report=True` against the actual Gmail API (reusing the existing
  OAuth token, no browser popup) — the report was sent successfully
  twice (once before, once after the scope-narrowing fix), confirming
  both that sending works and that the fix resolved the shared-file
  side effect.

## Acceptance criteria (met)

- Email body is JSON-only, no free text.
- Recipient, GitHub repo, and group name are config-driven.
- Every Gmail call goes through the rate-limited `ApiGatekeeper`.
- Real send verified against the actual API; the shared token file's
  scopes are left untouched by this project.
- `send_report` defaults to `False`; no test or casual run sends a real
  email unless explicitly requested via the dedicated CLI entry point.
