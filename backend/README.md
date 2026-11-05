# Backend

FastAPI application in `second_brain/`, managed by the root uv project. Follow the [local setup](../README.md#run-locally) and [deployment guide](../DEPLOYMENT.md).

## Source map

| File | Responsibility |
| --- | --- |
| `api.py` | Same-origin routes, access gate and browser workspace identity |
| `service.py` | Owned transactions, task edits, history, chat and model-output validation |
| `muse.py`, `internet_muse.py` | Meta planning, structured responses and native web search |
| `voice.py` | Meta audio transcription |
| `attachments.py` | File validation, extraction and model input |
| `sample.py` | One-time illustrative starter content; no model calls |
| `db.py`, `migrations/` | SQLAlchemy records and Alembic migrations |

## Configuration

The root `.env` supplies local configuration; process environment overrides it. See [.env.example](../.env.example) for names and defaults. SQLite defaults to `backend/second-brain.db`. Hosted deployments require PostgreSQL and either public-demo opt-in or an access code. Meta credentials stay server-side.

New, untouched workspaces receive sample data when `SAMPLE_WORKSPACE=true` (default). Tasks, sample context, a TXT attachment and history commit atomically under the workspace lock. Saved work and cleared workspaces are not repopulated. Samples are labeled, use illustrative handoff assessments and contain no assistant replies or simulated model successes.

Tasks and their subtasks share a root-task conversation. General chat is separate. Muse updates are validated before persistence; errors preserve saved state. Handoff means internet-enabled chat research or drafting, not browser or desktop execution. Retired browser tables/migrations remain to preserve old data.

Attachments accept PDF, TXT, DOCX and PNG/JPEG/WebP/GIF: five per message, 4 MB each. Original files persist in the workspace database. PDF/images use Meta's multimodal input; TXT/DOCX provide extracted text. Voice capture allows three minutes, transcribes in small parts and fills an editable draft before sending.

## Checks

```powershell
uv run pytest
uv run ruff check backend frontend scripts
```

Tests use temporary databases and explicit model fixtures. They cover ownership, persistence, validation, retry behavior, chat scopes, file handling and frontend interactions. `/dev` shows workspace-scoped read-only diagnostics; `/docs` exposes the API reference. Health reports liveness, not proof of model availability.
