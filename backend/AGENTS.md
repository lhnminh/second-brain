# Backend instructions

These instructions supplement the root `AGENTS.md`. Read it and
`../visual_second_brain_spec.md` before making product or architecture changes.
Explain changes step by step and preserve the other developer's work.

## Ownership

Own server-side implementation in `backend/`:

- Authentication integration and per-user authorization.
- Persistent task, subtask, user-context, message, and agent-activity records.
- Schema migrations, API behavior, input validation, and error handling.
- Muse integration for text/voice input, text replies, subtask creation, and scoring.
- Voice-input processing or forwarding, according to the verified Muse contract.
- Planning activity status and validated dashboard updates.

The root uv project manages all Python dependencies, its lockfile, virtual
environment, and Python version. The `second_brain` package lives in
`backend/second_brain/`; do not create a separate backend uv project. The service
uses FastAPI and SQLAlchemy/Alembic, with Neon for hosted persistence and SQLite
for local development. Coordinate root configuration changes and update the
README as part of those changes.

## Data and agent rules

- Tasks and subtasks share a structure, linked by `parent_task_id`. Enforce
  ownership on every operation, prevent cross-user parents, and prevent cycles.
- Deadlines are optional. Do not invent dates when decomposing a task.
- Validate `importance_score` as an integer from 0–100, or unset until assessed.
  A user-selected importance level constrains scoring to that level's range.
- Importance is separate from deadline urgency and derived priority. Agree the
  five ranges and ranking behavior before implementing them.
- Store structured user context with sources, update times, and whether it was
  user-stated, confirmed, or inferred. Preserve user corrections.
- An agent planning run is separate from the user's task status. Creating
  subtasks or scoring a task does not complete the underlying work.
- The MVP agent creates subtasks and scores importance. External execution,
  screen capture, and spoken replies are deferred.

## Muse and frontend boundary

- Verify Muse's actual API and available capabilities before implementing calls.
  Keep provider behavior behind an adapter and credentials server-side. Do not
  introduce a different provider without an explicit decision.
- Validate generated updates before persistence. Handle stale updates, duplicate
  submissions, and failures without destroying user work or inventing success.
- Coordinate task, context, message, activity, error, and authentication contracts
  with the frontend developer. Record the agreed shapes and endpoints in a
  shared root-level contract document when defined.
- Document how the frontend submits voice input and receives text replies,
  activity, and resulting task changes. Do not assume a transport is selected.
- Own changes inside `backend/`. Coordinate frontend or shared root-file changes
  with the other developer; communicate contract changes before applying them.
- Keep configuration examples free of secrets and distinguish fixtures from real
  Muse behavior.

## Verification

As functionality is added, prioritize checks for cross-user isolation, task
relationships, importance bounds and user constraints, generated-output
validation, persistence, and failure recovery. Validate an end-to-end text input
through Muse to a saved task update before expanding the voice integration.
