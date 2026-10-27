# Visual Second Brain

**A new way to interact with AI agents. The future is visual.**

Working with an AI agent should feel as natural as seeing a plan take shape.
Your priorities, tasks, next steps, and the agent's activity belong in a shared
space you can understand at a glance and change directly.

Visual Second Brain is building that space: a daily dashboard where you and your
agent work together. Start with a mostly blank canvas, tell Muse what you need to do, and watch a
reviewable plan take shape. Return to saved work when you need it. Less time reconstructing context. More room to
think and get things done.

## See it. Shape it. Move forward.

The vision goes beyond a conversation window. You shouldn't have to describe
every change in a message or scroll through a transcript to find out what is
happening. The interface itself should be how you steer the work.

- **See what matters.** Bring priorities, commitments, and next actions into view.
- **Shape the plan directly.** Edit a task, adjust its importance, or revise a
  suggested step where it appears.
- **Understand the agent's work.** See its planning activity and inspect what it
  proposes before accepting changes.
- **Carry your context forward.** Return to a workspace that remembers your
  corrections and the work you've already done.
- **Talk when it helps.** The broader experience includes a corner companion
  for conversation and voice input, alongside direct dashboard interaction.

The goal is to free up time and mental space. You bring the intent; the agent
helps turn it into a plan you can see and steer.

## The first experience

You have homework due next Sunday. Tell Muse through chat, answer any questions,
and review the proposed task and steps. Revise the proposal through conversation,
edit a step directly, and save it when it feels right. The canvas renders those
saved objects as cards. Mark work complete, return later, and pick up where you left off.

The current prototype supports conversation-based task creation and corrections,
task and subtask editing, five importance levels, saved context, real Muse planning,
and review before saving. `/dev` provides a read-only developer console for model runs, request inputs,
proposals, saved objects, and change history. It uses a shared demo account protected by an access token.
Microphone recording and Meta transcription feed the reviewed text conversation (see `frontend/README.md`).
Automatic onboarding, an animated companion, and real sign-in remain
incomplete. The agent helps plan work; it does not execute the underlying tasks.

## Try it locally

From the repository root:

```sh
cp -n .env.example .env
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run second-brain
```

Add your `META_API_KEY` to `.env` to enable Muse planning. Keep credentials in
that ignored file. Open [localhost:8000](http://localhost:8000/) for the dashboard
or [/dev](http://localhost:8000/dev) for diagnostics and saved objects.
A successful demo login stays connected across both pages and reloads for eight
hours; use Sign out to end this browser session.
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
