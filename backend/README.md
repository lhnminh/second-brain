# Backend

First slice: user context and homework task → Muse breakdown → user review →
persisted subtasks and corrections. Python/FastAPI, SQLAlchemy, Alembic, Neon
(Postgres). SQLite is a local-development/test option only.

## Local setup

From the repository root:

```sh
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.app:app --reload --port 8000
```

Open `http://localhost:8000/` for the quick dashboard or `/docs` to exercise the
API. All Python dependencies and
development tools use the root `pyproject.toml`, `uv.lock`, `.venv`, and Python
3.14 selection. There is no separate backend uv project. The root package builds
from `backend/second_brain/`, replacing the original hello-world scaffold.
`uv run second-brain` also starts the service, without automatic reload.

Configuration loads the root `.env`, with process environment taking precedence.
Empty values use defaults. Do not put secrets in tracked files.

| Variable | Purpose / default |
| --- | --- |
| `DATABASE_URL` | Neon Postgres connection URL with SSL; default local SQLite file `backend/second-brain.db` |
| `MOCK_USER_ID` | Workspace namespace (keep stable); `demo-user` |
| `MOCK_AUTH_TOKEN` | Optional local demo bearer token; required on Vercel |
| `META_API_KEY` | Existing Meta key; required for real planning |
| `META_BASE_URL` | `https://api.meta.ai/v1` |
| `META_MODEL` | `muse-spark-1.3` |
| `FRONTEND_ORIGIN` | Allowed browser origin; `http://localhost:3000` |

Run migrations explicitly before starting the app and before each deployment;
startup does not create tables. Neon URLs beginning `postgres://` or
`postgresql://` are normalized to the psycopg SQLAlchemy driver. Postgres uses
short-lived connections (`NullPool`) for serverless operation. Preserve the SSL
parameters from Neon. Never use SQLite on hosted Vercel filesystem storage.
The default SQLite path is absolute and independent of the working directory,
so data saved before uv consolidation remains at the same location. Explicit
relative SQLite URLs are resolved from the command's working directory.

## Reproducible homework demo

Use `/docs` and the request shapes in [API_CONTRACT.md](../API_CONTRACT.md):

1. Save context through `PUT /api/context/studies` with `expected_version: 0`.
2. Create “Finish homework”, date `2026-11-01` (Sunday following the October 26
   scenario), importance `high`. The API accepts explicit dates, not relative
   phrases; confirm any exact deadline with the user in the UI.
3. Ask for a breakdown using a fresh request UUID. Inspect the run's status,
   saved reply, and proposal. Tasks remain unchanged during review.
4. Edit the proposed steps if needed; approve the reviewed proposal.
5. Edit a saved subtask or its importance with its current version.
6. Reload the dashboard or restart the server; the corrections remain saved.

Unknown assignment requirements should lead to clarification, not fabricated
details. No submission time is inferred. Rejection and failed planning preserve
the task. Planning success never means the homework is completed.

## Checks

From the repository root:

```sh
uv run pytest -q
uv run ruff check backend
uv run ruff format --check backend
uv run alembic -c backend/alembic.ini check
```

Tests migrate an isolated SQLite database and use an explicitly named
`FixtureMuse`; application code never selects that fixture. They exercise the
saved homework journey, review edits, owner isolation, version conflicts,
invalid model output, duplicate planning/approval, failed/interrupted calls,
and user corrections. SQLite results do not establish Neon/Postgres behavior;
run the same journey against a development Neon database before deployment.

For an opt-in live Meta smoke check using only a disposable local database:

```sh
uv run python -m second_brain.smoke
```

This sends synthetic homework context to the configured Meta endpoint, makes one
billable request, validates the response, approves the proposal, reloads saved
data, and removes the temporary database. It prints only status/counts, never
the API key or provider response. It does not touch your configured database.

Initial verification on October 26, 2026: 30 tests passed; Ruff lint/format,
Alembic upgrade/schema-drift checks, and Git whitespace checks passed. A live
vague-homework prompt returned a clarifying reply with no invented subtasks. A
second live call with a concrete synthetic assignment produced six subtasks;
approval and a later user correction persisted after reconnecting to SQLite.
Neither initial check used Neon or a deployment. Subsequent local frontend
verification is recorded in [frontend/README.md](../frontend/README.md).

## Hosting and limits

Vercel project root: the repository root. The exported FastAPI app is
`backend/app.py`; dependency configuration and the `backend.app:app` entrypoint
live in the root `pyproject.toml`. Configure
Neon, the Meta key, mock owner/token, and the frontend origin as server-side
environment variables, then apply migrations explicitly. Deployment has not
been performed by this implementation.

The hackathon uses isolated anonymous browser workspaces behind a shared demo
access gate. Ownership is enforced at the service/database boundary. Individual
sign-in, recovery, and cross-device linking are on the roadmap. Inferred onboarding context,
streaming, pagination, and automatic priority ranking are deferred. Calls are
synchronous with a 45-second model timeout; ensure the deployment's function
duration accommodates this. `/health` is liveness, not external readiness.

Integration references verified October 26, 2026:
[Meta overview](https://dev.meta.ai/docs/overview),
[Meta structured output](https://dev.meta.ai/docs/structured-output),
[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi).

## Conversation canvas

The homepage now uses `POST /api/conversation` to start planning without an
existing task. Muse returns validated task objects and their subtasks, or a
clarifying text reply. Acceptance through `/api/conversation/{id}/approve` applies
all reviewed objects in one transaction. The original task-specific planning
endpoint remains available through the API. `/dev` is a read-only diagnostic
console for runs, request inputs, proposals, messages, saved objects, and events. See `API_CONTRACT.md` for shapes and retry/review behavior.

Run `uv run alembic -c backend/alembic.ini upgrade head` before starting an updated
checkout. The conversation migration preserves task-planning history, permits a
null `task_id` on runs, and adds validated request inputs for retries and inspection.
Automatic onboarding extraction remains incomplete; individual sign-in is roadmap work.

### Dashboard-focused model guidance

The model instructions make task cards and bite-size steps the main planning
output. Titles and descriptions should be useful with chat closed. Chat briefly
explains the proposed cards and invites review instead of repeating the plan.
Concrete commitments can produce a card with unknown details left unset; missing
assignment requirements call for a focused question rather than invented steps.
For a Duolingo take-home without a brief, the model should propose the take-home
and reviewing its brief, then ask for assignment details before specific work.

This is prompt tuning, not model weight fine-tuning. The provider, schemas, and
review-before-save contract are unchanged. The automated take-home journey uses
a mocked provider response through the real adapter to verify review, correction,
and persistence; it does not measure live model adherence to these instructions.


## Shared browser session

The workspace and dev console use `/api/session` to exchange the configured demo
access token for a signed eight-hour HttpOnly cookie. It survives navigation and
reloads; the bearer API remains available. No new migration is needed for sessions.
Access sessions are workspace-bound and signed with the configured demo token;
token rotation invalidates access across workers without changing saved ownership.
A separate random HttpOnly workspace cookie lasts one year, renewed on use, and
survives sign-out and server restarts. HTTPS and Vercel use Secure cookies. Both
pages clear private rendered state on 401 and expose sign-out. Clearing workspace
cookies or switching browser profiles starts a separate workspace with no recovery.
Existing shared-owner data is retained but not assigned to new browsers. No schema
migration is needed. Bearer API clients must retain cookies between requests.
See `API_CONTRACT.md` for expiry and origin rules.


October 27 browser-workspace verification: 91 automated tests passed using isolated
SQLite databases and fixture model responses. Coverage includes same-token browser
isolation across tasks/context/messages/runs/events, foreign-record rejection,
saved-state return through a fresh app instance, sign-out/reconnect, access expiry,
token rotation, workspace/session mismatch, and clearing cookies. Ruff lint/format
and Git whitespace checks passed. These checks do not verify hosted Neon/Vercel.
