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
| `MOCK_USER_ID` | Server-selected demo owner; `demo-user` |
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

This is a single-account mock-auth demo, not public multi-user authentication.
User ownership is enforced at the service/database boundary. Add verified
sign-in before public use. Voice, inferred onboarding context, general chat,
streaming, pagination, and automatic priority ranking are deferred. Calls are
synchronous with a 45-second model timeout; ensure the deployment's function
duration accommodates this. `/health` is liveness, not external readiness.

Integration references verified October 26, 2026:
[Meta overview](https://dev.meta.ai/docs/overview),
[Meta structured output](https://dev.meta.ai/docs/structured-output),
[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi).
