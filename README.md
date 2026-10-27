# Visual Second Brain

**A new way to interact with AI agents. The future is visual.**

Working with an AI agent should feel as natural as seeing a plan take shape.
Your priorities, tasks, next steps, and the agent's activity belong in a shared
space you can understand at a glance and change directly.

Visual Second Brain is building that space: a daily dashboard where you and your
agent work together. Open it in the morning, see where things stand, and decide
what deserves your attention. Less time reconstructing context. More room to
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

You have homework due next Sunday. Add the assignment and its deadline, tell
Muse what it needs to know, and ask for a breakdown. The suggested steps appear
for review. Rewrite a step, remove one that doesn't help, and save the plan when
it feels right. Mark work complete as you go. Come back later and pick up where
you left off.

The current prototype supports task and subtask editing, five importance levels,
saved context, real Muse planning, review before saving, and planning history.
It uses a shared demo account protected by an access token. Voice input,
automatic onboarding, an animated companion, and real sign-in are still ahead.
The agent currently helps plan work; it does not execute the underlying tasks.

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
or [/docs](http://localhost:8000/docs) for the API explorer.

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
