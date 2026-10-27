# Conversation canvas and development workspace

The browser assets live in `dashboard.py`, following the repository's `.py`
source convention. FastAPI serves the canvas at `/` and development tools at
`/dev`. Both call the same-origin API; no frontend framework or build is needed.

From the repository root:

```sh
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run second-brain
```

Open `http://localhost:8000/`. Restart an existing server after updating Python
routes or backend code. UI asset edits appear on page reload. For automatic
backend reload, use `uv run uvicorn backend.app:app --reload --port 8000`.

## Main journey

1. Start with a quiet canvas and tell Muse what needs doing. No task form is required.
2. Answer clarifying questions or review the task objects and steps Muse proposes.
3. Revise through chat or edit proposed titles, descriptions, and deadlines directly.
   You can remove unwanted tasks or steps. Follow-up messages carry unsaved edits.
4. Save the reviewed plan. Persisted task objects become cards on the canvas.
5. Edit saved tasks, choose among five importance levels, or mark work complete.
6. Return to saved tasks and conversation history. Re-enter the demo access token
   after reload if authentication is configured.

Model proposals remain separate from saved work until accepted. Conversation
corrections can update existing task objects; steps append to existing plans.
The model can correct an existing step by ID. The UI renders fixed task components,
not generated HTML or arbitrary widgets. See `API_CONTRACT.md` for object shapes.

## Development tools

`/dev` retains the previous manual task/context forms, task-specific planning,
proposal review, and planning activity. Expand **Inspect saved objects** to see
owned tasks, context, messages, runs (including request inputs and proposals), and
change events. Conversation proposals are reviewed on the canvas. Both pages
use the same API authentication; the HTML shells embed no credentials.

There are no seeded objects or simulated model responses in either page. The
Meta key stays server-side. The demo token stays in page memory. Browser drafts
survive in-page request failures, but unsaved edits are not persisted across
navigation or reload. A network retry reuses its request ID and input. Voice,
automatic onboarding extraction, real sign-in, arbitrary widgets, and task
execution remain incomplete.

## Verification

October 26, 2026: browser checks used an isolated SQLite database and real Muse
Spark. Chat created a two-step homework proposal, a follow-up revised that plan,
and a direct edit was saved before approval. The canvas displayed saved objects
and completion updates. Saved edits and completion survived reload; a rename
proposal updated the same task, and the `/dev` inspector showed those records.
A stopped-server check preserved the chat draft and saved cards. Automated fixture tests cover creation, revisions,
clarifying replies, invalid model output, retries, preservation of corrections,
owner isolation, stale proposals, and upgrading existing task-planning data.
Hosted deployment and Neon are not verified by these checks.

The narrow mobile layout is included in CSS but has not been visually verified.
