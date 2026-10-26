# Backend API contract — first implementation

Status: implemented backend contract; the quick dashboard's core task/planning
flow has been verified locally in a browser. All paths are relative to the backend origin. JSON request and
response bodies use snake_case. Interactive schemas: `/docs`; machine schema:
`/openapi.json`.

## Identity and transport

For this MVP, identity is the server's `MOCK_USER_ID` (default `demo-user`). The
client cannot choose an owner in a header or body. This is a single-account demo,
not real sign-in. Every read and write is scoped to that server-selected owner.
Tests use separate configured identities against the same database.

If `MOCK_AUTH_TOKEN` is configured, every `/api/` request requires
`Authorization: Bearer <demo token>`. This shared demo token is not the Meta key.
Hosted Vercel instances refuse to start without this token and a Postgres URL.
Use deployment protection for a private demo. Real account authentication and
authorization through verified identity remain a follow-up before public use.

`FRONTEND_ORIGIN` allows one CORS origin (default `http://localhost:3000`).
Credentials and `user_id` are not accepted in request bodies. Dates use
`YYYY-MM-DD` without a guessed submission time; timestamps are UTC ISO strings.
UUIDs identify tasks, runs, and messages. Context IDs are 1–100 ASCII letters,
digits, underscores, or hyphens.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/` | Same-origin quick dashboard; public shell without embedded credentials |
| GET | `/health` | Service liveness, configured model, mock-auth indicator; does not claim DB or model readiness |
| GET | `/api/dashboard` | Owner's tasks, context, runs, messages, events |
| GET | `/api/importance-levels` | Five accepted level ranges |
| POST | `/api/tasks` | Create task or subtask; returns task, HTTP 201 |
| PATCH | `/api/tasks/{id}` | Edit with `expected_version`; returns updated task |
| PUT | `/api/context/{key}` | Create/correct structured context with `expected_version` |
| POST | `/api/tasks/{id}/plans` | Send text to Muse; persist conversation and return reviewable run |
| POST | `/api/runs/{id}/approve` | Atomically apply a reviewed proposal |
| POST | `/api/runs/{id}/reject` | Reject without changing work |

Errors: `{"error":{"message":"..."}}`. Validation errors additionally include
`fields`, each with `path` and `message`, excluding submitted values. HTTP 401:
demo authentication; 404: missing or another owner's record; 409: stale state or
reused request key with different input; 422: invalid input or score constraint;
503: database failure. A completed planning request returns HTTP 200 with a run
whose `status` can be `failed`; inspect status, not just HTTP success.

## Task records and edits

Create example:

```json
{
  "title": "Finish homework",
  "description": "Assignment details still need clarification",
  "deadline": "2026-11-01",
  "user_importance_level": "high",
  "parent_task_id": null
}
```

Only `title` is required. Description defaults to empty, all other inputs to
null. Response adds `id`, `user_id`, `importance_score` (initially null), `status`
(`pending`), sibling `position`, `version` (1), `created_at`, and `updated_at`.
Titles are 1–300 characters; descriptions and context/message text at most
10,000 characters. Unknown fields are rejected.

PATCH accepts `expected_version` and any subset of `title`, `description`,
`deadline`, `user_importance_level`, `status`. Null clears deadline or user level;
title, description, and status cannot be null. Status values: `pending`,
`in_progress`, `completed`. An edit increments version. A mismatch returns 409.
Clients cannot write `importance_score` directly.

Parent links are immutable in this slice: children may only reference existing
tasks of the same owner, preventing cycles. Siblings append in `position` order.
Parent completion is manual. Deadlines, scores, and completion do not propagate.
These are initial implementation choices, not automatic rollup behavior.

## Importance

| Value / UI label | Internal score |
| --- | --- |
| `very_low` / Very low | 0–19 |
| `low` / Low | 20–39 |
| `medium` / Medium | 40–59 |
| `high` / High | 60–79 |
| `very_high` / Very high | 80–100 |

Display the selected level, or the range containing the agent score when no user
level exists. Null score with no user level means unassessed. Reject model scores
outside a user-selected range. Changing a user level clamps an existing score to
the new range; an unassessed task stays unassessed. Removing a user level leaves
the existing score in place. Deadline urgency and dashboard priority ordering
are not implemented; the API does not claim an importance sort is priority.

## Structured context

PUT `/api/context/studies`:

```json
{
  "expected_version": 0,
  "category": "current_situation",
  "content": "I am studying part time",
  "provenance": "user_stated"
}
```

Version 0 creates; later edits must supply the current version. Categories:
`about_user`, `long_term_direction`, `current_situation`,
`assistance_preferences`. Provenance: `user_stated` or `user_confirmed`.
Returns the saved record with `id`, owner, incremented `version`,
`source: direct_user_edit`, and update timestamp. Prior values remain in events.
Model calls receive the latest structured context. This slice does not infer or
save onboarding context automatically, and context never grants permissions.

## Text → proposed plan → review → saved tasks

POST `/api/tasks/{id}/plans`:

```json
{"request_id":"8a9883da-52c7-47d1-8715-5988f0958e1e","message":"Help me break down my homework"}
```

`request_id` is a client-generated UUID. Retry the same request using the same
ID; it returns the original run without another model call. Different input with
the same ID returns 409. For an intentional new plan, use a new UUID.

Run records include `id`, `user_id`, `task_id`, `request_id`, `message`,
`snapshot_revision`, `status`, `proposal`, `error`, `model`, timestamps.
States: `running` → `awaiting_review`, `stale`, or `failed`;
`awaiting_review` → `applied`, `rejected`, or `stale`.

The request is synchronous (model timeout 45 seconds); it does not enqueue work
or stream tokens. A separate dashboard poll can observe persisted activity.
Running records older than two minutes are marked failed on dashboard read to
recover interrupted invocations. The user message is saved even on model failure.
Persisted assistant messages carry the model's text reply, not synthetic success.
Conversation is currently task-planning text only, not a general chat endpoint.

Proposal:

```json
{
  "reply": "Review these steps before saving.",
  "importance_score": 70,
  "subtasks": [
    {"title":"Read assignment instructions","description":"Check requirements","importance_score":65}
  ]
}
```

The adapter validates strict integer scores, shape, text limits, maximum 20
subtasks, and the parent's selected importance range. There is no deadline field
in generated subtasks. A vague assignment can produce a clarifying text reply
and no subtasks. No external execution happens.

Approve with `{}` to apply the original proposal, or
`{"proposal": <edited full proposal>}` to apply reviewed edits. Approval inserts
subtasks and updates the parent's score in one transaction. It does not change
the parent's title, deadline, selected level, or completion status. Repeated
approval/rejection is idempotent. Existing children are preserved and new ones
append; a fresh plan is not a replacement operation.

Any task or context change for the owner invalidates outstanding proposals. A
stale approval returns 409; request a fresh plan with a new UUID. This conservative
rule preserves corrections even when planning overlaps user edits. Concurrent
approvals serialize through the owner's account row to avoid duplicate effects.

## Deferred

Voice/transcription, automatic onboarding extraction, general conversation,
real sign-in, pagination, deletion, automatic priority ranking, and execution of
the homework itself. The quick frontend is described in `frontend/README.md`.
