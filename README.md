# Visual Second Brain

A daily dashboard that turns what's on your mind into a plan you can see, edit and act on.

**[Open the live app](https://second-brain-iota-blue.vercel.app/)** · Built for the Meta Global AI Developer Hackathon by Minh Le and Ulvi.

- Short-term tasks, long-term goals, deadline urgency and an interactive bubble map.
- Direct editing, subtasks, completion history and reversible deletion.
- Muse chat with web search, task-specific history, file attachments and voice input.
- Persistent, separate workspaces for each browser. New visitors get editable example tasks.

Muse Spark (`muse-spark-1.3`) handles planning, research and drafting; Muse Voice (`muse-voice-transcribe-1.0`) transcribes recordings. Handoff returns work in task chat. It does not control your computer.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from the repository root:

```powershell
uv sync
Copy-Item .env.example .env  # First setup only; keep an existing .env
```

Set `META_API_KEY` in `.env` to your Meta Model API key. Leave `DATABASE_URL` blank for local SQLite. Without a key, the dashboard and manual editing work; AI and transcription require active API access.

```powershell
uv run alembic -c backend/alembic.ini upgrade head
uv run second-brain
```

Open [localhost:8000](http://localhost:8000/). Keep using the same browser and hostname to retain your workspace. The project uses Python 3.14, which uv can install automatically. After pulling updates, rerun `uv sync` and the migration command, then restart.

## Development

FastAPI · Python-rendered HTML/CSS/JavaScript · SQLAlchemy/Alembic · SQLite locally / PostgreSQL on Supabase for the live app · Vercel.

```powershell
uv run pytest
uv run ruff check backend frontend scripts
```

[/dev](http://localhost:8000/dev) is a read-only console for your workspace's real model requests, saved objects and changes. Example context is labeled and excluded from model-run counts. Credentials stay server-side; `.env` files and databases are ignored.

[Deployment and manual updates](DEPLOYMENT.md) · [Backend](backend/README.md) · [Frontend](frontend/README.md) · [Product specification](visual_second_brain_spec.md)
