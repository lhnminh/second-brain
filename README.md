# Visual Second Brain

A daily dashboard to help free up time and mental space. See
[the product spec](visual_second_brain_spec.md) for the current direction.

## Two-person development

| Folder | Owner's scope | Instructions |
|---|---|---|
| `frontend/` | Dashboard, task editing, onboarding UI, pet, chat, microphone controls | [Frontend AGENTS.md](frontend/AGENTS.md) |
| `backend/` | Auth, per-user data, APIs, Muse integration, voice processing, scoring | [Backend AGENTS.md](backend/AGENTS.md) |

Both follow the root [AGENTS.md](AGENTS.md) and the product spec. Agree the task,
context, message, activity, and API contracts together before integrating. Record
those contracts in a shared root-level document when defined. Frontend work can
use clearly labeled fixtures while the backend implements the agreed behavior.

The backend now contains a runnable FastAPI service with SQLAlchemy/Alembic
persistence, a Meta Muse adapter, and review-before-saving task proposals.
See [backend setup and demo](backend/README.md) and the shared
[API contract](API_CONTRACT.md). Neon is the hosted database; SQLite supports
local development and automated tests. A small browser dashboard at `/` connects
to these APIs for tasks, context, Muse planning, and review before saving.
Python dependencies, the lockfile, and the virtual environment are managed at
the repository root. The root package points to application code in
`backend/second_brain/`; the original hello-world placeholder has been replaced.

Run from the repository root:

```sh
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run second-brain
```

Open `http://localhost:8000/` for the dashboard or `/docs` for the API explorer.
Restart an already-running server after pulling changes. Run checks with
`uv run pytest`.

Hosted setup is documented in [DEPLOYMENT.md](DEPLOYMENT.md). GitHub source,
Neon migrations, and Vercel deployment are separate steps; credentials remain in
server-side configuration.

First integration milestone: a signed-in user sends text through the pet to Muse
and sees a task update persisted to their own account. Then expand onboarding,
voice input, and the dashboard. Coordinate shared root-file and contract changes
between both developers.

## Local environment

Create your local configuration if `.env` does not already exist:

```sh
cp -n .env.example .env
```

Keep credentials in `.env`, which Git ignores. The tracked `.env.example`
contains blank secret placeholders and non-secret defaults. Keep it updated when configuration changes.

The backend loads this root `.env`. `META_API_KEY` authenticates real Meta calls;
`META_BASE_URL` and `META_MODEL` default to the verified Meta endpoint and Muse
Spark 1.3. Additional backend
configuration and known limits are documented in [backend/README.md](backend/README.md).
