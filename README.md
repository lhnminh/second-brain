# Visual Second Brain

**A new way to interact with AI agents. The future is visual.**

Working with an AI agent should feel as natural as seeing a plan take shape.
Your priorities, tasks, next steps, and the agent's activity belong in a shared
space you can understand at a glance and change directly.

Visual Second Brain is building that space: a daily dashboard where you and your
agent work together. Start with a mostly blank canvas, tell Muse what you need to do, and watch a
actual tasks take shape on the dashboard. Return to saved work when you need it. Less time reconstructing context. More room to
think and get things done.

## See it. Shape it. Move forward.

The vision goes beyond a conversation window. You shouldn't have to describe
every change in a message or scroll through a transcript to find out what is
happening. The interface itself should be how you steer the work.

- **See what matters.** Bring priorities, commitments, and next actions into view.
- **Shape the plan directly.** Edit a task, adjust its importance, or revise a
  suggested step where it appears.
- **Understand the agent's work.** See its planning activity, saved changes, and
  which tasks can be handed off to Muse.
- **Carry your context forward.** Return to a workspace that remembers your
  corrections and the work you've already done.
- **Talk when it helps.** The broader experience includes a corner companion
  for conversation and voice input, alongside direct dashboard interaction.

The goal is to free up time and mental space. You bring the intent; the agent
helps turn it into a plan you can see and steer.

## The first experience

You have homework due next Sunday. Tell Muse through chat and the task appears
on your dashboard with useful steps. Answer a focused question if details are
missing, then change the saved task directly or through a follow-up message.
There is no separate proposal form or save-plan step. Mark work complete, return
later, and pick up where you left off.

The current prototype supports manual and conversation-based task creation and corrections,
task and subtask editing, five importance levels, saved context, real Muse planning,
and direct saving of validated task updates. `/dev` provides a read-only developer console for model runs, request inputs,
proposals, saved objects, and change history. Each browser has its own saved workspace, protected by a shared demo access token.
Microphone recording and Meta transcription feed the reviewed text conversation (see `frontend/README.md`).
Automatic onboarding and an animated companion remain incomplete. Individual sign-in
is on the roadmap after the hackathon. The agent helps plan work; it does not execute the underlying tasks.

## Try it locally

From the repository root:

```sh
cp -n .env.example .env
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run second-brain
```

Manual creation, editing, completion and reopening work without an API key.
Use **+ Add task** beside either focus count: short-term tasks take named
subtasks, while long-term tasks take a description. Entered steps save together
with the short-term task, without a model call. Apply all migrations first; migration
`c42b193d7e61` adds the saved focus-section choice without moving existing tasks.

Add your `META_API_KEY` to `.env` to enable Muse planning. Keep credentials in
that ignored file. Open [localhost:8000](http://localhost:8000/) for the dashboard
or [/dev](http://localhost:8000/dev) for diagnostics and saved objects.
A successful demo connection lasts eight hours across both pages and reloads.
Sign out ends access while keeping this browser’s workspace. A separate workspace
cookie lasts one year, renewed on use; clearing cookies or switching browsers
starts a new workspace.

On Windows, copy `.env.example` to `.env` if it does not exist. Get a Meta
Model API key from your team's Meta developer account and put it after
`META_API_KEY=`. This project's variable name is `META_API_KEY`; Meta's general
quickstart uses `MODEL_API_KEY`, which this app does not read. The existing
`META_BASE_URL=https://api.meta.ai/v1` and `META_MODEL=muse-spark-1.3` defaults
match the configured adapter. Never use the website demo access token as a model
key. Do not commit `.env` or paste the key into chat.

Restart the backend after saving the key (`Ctrl+C`, then `uv run second-brain`
from the repository root). Open the live workspace at
[127.0.0.1:8000](http://127.0.0.1:8000/), or choose **My workspace** from sample
mode. Use the same hostname/browser to keep your workspace. Try: “Create a task
to prepare for an interview on November 6, 2026, with three subtasks.” Check
the resulting cards, open **Task chat**, send a correction, and reload to check
saved tasks and history. Inspect failed runs in `/dev` without exposing secrets.
Model billing/access and credits must be active in the Meta account.

Hosted testing uses the server's key configured in Vercel. A local `.env` change
does not configure or deploy the hosted site. Computer handoff remains a separate,
unimplemented worker connection; no laptop or cloud computer is connected by
adding the model key.
The API explorer is at [/docs](http://localhost:8000/docs). After updating an
existing checkout, run the migration command above and restart the server.

All Python dependencies use the root uv project. The app uses FastAPI,
SQLAlchemy/Alembic, and Meta Muse Spark, with Neon for hosted persistence and
SQLite for local development. Run checks with `uv run pytest`.

## Explore the project

- [Product specification](visual_second_brain_spec.md) — direction, scope, and open decisions.
- [Frontend](frontend/README.md) — the dashboard and its current interactions.
- [Backend](backend/README.md) — setup, persistence, model integration, and verification.
- [API contract](API_CONTRACT.md) — the shared frontend/backend boundary.
- [Deployment](DEPLOYMENT.md) — GitHub, Neon, and Vercel setup.
- [Contributor instructions](AGENTS.md) — how we build and collaborate.
