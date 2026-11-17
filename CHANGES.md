# Fix round — 2026-11-17

Review of the full tree (worker agent, controller, dashboard, infra). Fixes only; no feature changes.

## Controller

- `app/crypto.py` — `FERNET_KEY` values that are not valid Fernet keys (e.g. the shipped `.env.example` value) made `Fernet()` raise on the first credential operation, so the documented `cp .env.example .env` deploy flow crashed on provisioning. Any passphrase now works: generated Fernet keys are used as-is, anything else derives a deterministic key via SHA-256. Roundtrip verified.
- `app/main.py` — `/health` reported `"redis": True` unconditionally; now an actual Redis ping.
- `app/services/docker_ctl.py` — a failed Docker connection was cached forever (`_client = False`); the socket appearing later never got picked up until restart. Failures are no longer cached.
- `app/routers/chat.py` — ingest auto-reply enqueued `run_script` tasks with `worker_id: None`, which no worker can ever claim. Auto-replies are now only enqueued when the message carries a `worker_id`.
- `app/routers/accounts.py` — provision created and committed the account, then could raise 400 "no worker available", leaving a dangling `provisioning` account with no task. Worker resolution happens first now.
- `app/services/tasks.py` — a naive `run_at` (client sends no TZ) crashed `enqueue_task` with a naive-vs-aware `TypeError` → 500. Naive datetimes are treated as UTC.

## Worker agent

- `agent/main.py` — heartbeat reported `"busy" if runtime.page else "idle"`; `page` is set once at startup and never cleared, so the fleet always showed busy. Real idle/busy is now tracked via `runtime.busy` around `run_claimed`.
- `agent/main.py` + `agent/kick.py` — captured chat was ingested with `channel: ""`. The channel slug is now parsed from the page URL (`kick.current_channel`).
- `agent/kick.py` — `attach_chat_listener` threw on the second call ("function already registered") and the whole call was swallowed upstream, so the MutationObserver was never re-injected after navigation. Registration is now idempotent; the observer re-injects on every attach (the in-page guard still prevents duplicates per document).
- `agent/tasks.py` — `send_message` used a substring check (`channel not in page.url`) that false-matches short slugs (`"a"` in `kick.com/abc`); now an exact normalized URL comparison against `kick.channel_url`.
- `agent/tasks.py` — `screenshot` task was a stub returning `{"snapshot": true}`; it now captures a real JPEG into the task result.

## Dashboard

- `app/accounts/page.tsx` — `e.currentTarget.reset()` ran after `await`; React nulls `currentTarget` once the event loop turns, so every successful provision threw `TypeError: Cannot read properties of null`. The form element is captured before the await.
- `app/scripts/page.tsx` — invalid JSON in the steps textarea caused an unhandled rejection and a silently dead form; parse errors are caught and surfaced.

## Infra / scripts

- `scripts/healthcheck.sh` — always targeted `127.0.0.1:8000`, but prod publishes only nginx (:80) and dev maps the controller to `CONTROLLER_PORT` (8020 in `.env.example`), so the documented `./scripts/healthcheck.sh` failed in both modes. It now tries `CONTROLLER_URL`, then `NGINX_HTTP_PORT`, then `CONTROLLER_PORT` from `.env`, falling back to :80 / :8000.
- `.env.example` — comment updated: any non-empty `FERNET_KEY` string works; rotate with `Fernet.generate_key()` before storing real credentials.

## Verification

- `python3 -m compileall` over `apps/` + `workers/`: clean.
- Import check: full controller app (28 routes) and worker agent import; crypto roundtrip with both a derived and a generated key; `current_channel`, `channel_url`, URL comparison, double-attach listener, naive `run_at` rule — all asserted.
- Dashboard: `tsc --noEmit` clean; `next build` succeeds (7 routes).
- Not verified (needs a Docker host): end-to-end compose stack, live Kick login/chat flows, VNC preview.
