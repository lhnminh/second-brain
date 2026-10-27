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

If `MOCK_AUTH_TOKEN` is configured, data requests require either an authenticated
browser session or `Authorization: Bearer <demo token>`. This shared demo token
is not the Meta key. The same account is used by both pages.
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
| GET | `/` | Conversation canvas; public shell without embedded credentials |
| GET | `/dev` | Read-only diagnostics console: runs, objects, messages, and events; API data requires the same demo authentication |
| POST | `/api/session` | Validate demo token and establish an eight-hour browser session |
| DELETE | `/api/session` | Clear this browser’s demo session |
| GET | `/health` | Service liveness, configured model, mock-auth indicator and `demo_access_required` boolean; does not claim DB or model readiness |
| GET | `/api/dashboard` | Owner's tasks, context, runs, messages, events |
| GET | `/api/importance-levels` | Five accepted level ranges |
| POST | `/api/tasks` | Create task or subtask; returns task, HTTP 201 |
| PATCH | `/api/tasks/{id}` | Edit with `expected_version`; returns updated task |
| PUT | `/api/context/{key}` | Create/correct structured context with `expected_version` |
| POST | `/api/voice/transcribe` | Validate a short WAV recording and return Meta transcript without saving it |
| POST | `/api/conversation` | Conversation → clarification or reviewable task objects |
| POST | `/api/conversation/{id}/approve` | Atomically apply reviewed conversation objects |
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
The task-specific endpoint remains available for development; the canvas uses
the conversation endpoint described below.

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

Streaming audio transcription, automatic onboarding extraction,
real sign-in, pagination, deletion, automatic priority ranking, and execution of
the homework itself. The quick frontend is described in `frontend/README.md`.

## Conversation → task objects → canvas

POST `/api/conversation` accepts `request_id` and `message` with the same limits
and retry rules as task planning. Optional `review_draft` carries a complete
`ConversationProposal` containing the user's current unsaved edits. Reusing an
ID with a changed message or review draft returns 409. Every new run stores its
validated `input_payload`; legacy runs leave that field null.

Muse receives owned tasks, structured context, recent messages and run states,
a UTC reference date, and any review draft. Relative dates are model interpretations:
the UI asks the user to confirm the proposed date before saving.

Conversation runs use `task_id: null`. Their proposal shape is:

```json
{
  "reply": "Review this homework plan.",
  "tasks": [{
    "task_id": null,
    "title": "Math homework",
    "description": "Chapter 3 questions 1–5",
    "deadline": "2026-11-01",
    "importance_score": 60,
    "subtasks": [{"title": "Read chapter 3", "description": "Review assigned material", "importance_score": 55}]
  }]
}
```

All object fields shown are required; `task_id` and `deadline` may be null.
Maximum 10 task objects, with at most 20 proposed subtasks each. Text and score
validation match the existing task-planning schema. Empty `tasks` means a text
answer or clarifying question: the run finishes as `answered` and creates no work.
A nonempty proposal awaits review. A successful follow-up proposal marks earlier
pending conversation proposals `superseded`, preventing duplicate acceptance.
A failed follow-up leaves the prior proposal available.

POST `/api/conversation/{run_id}/approve` accepts `{}` or
`{"proposal": <complete edited conversation proposal>}`. Null task IDs create new
root tasks. Existing task IDs propose updates to owned task fields: title,
description, deadline, and importance score. Existing user importance choices,
completion status, parent links, and children are preserved. Subtasks append;
to correct an existing step, propose that step's ID with an empty subtasks list.
Ownership, duplicate task references, user score ranges, and snapshot revision
are checked again at approval. All objects and audit events save atomically.
The task-plan and conversation approval endpoints reject mismatched run types.
`POST /api/runs/{id}/reject` dismisses either proposal type.

The frontend renders these data objects with fixed components; Muse does not
produce HTML, executable scripts, arbitrary widgets, or external actions.
Conversation messages and proposals persist; unsaved browser edits survive
in-page request failures but not navigation/reload. The demo access token stays
only in the login form until submitted; a signed HttpOnly session cookie keeps
both pages connected through navigation and reload.

## Browser demo session

POST `/api/session` accepts `{"token":"<demo access token>"}`. With a configured
`MOCK_AUTH_TOKEN`, valid input returns `{"authenticated":true,"authentication":"mock"}`
and a signed session cookie. Invalid credentials return 401; input errors never
echo credentials. The cookie contains a random nonce, expiry, and HMAC signature,
not the access token. It is bound to the configured owner and signed with the
configured demo token, so owner or token changes invalidate existing sessions.
The session works across serverless workers without an in-memory session store.

The cookie is HttpOnly, SameSite=Strict, scoped to `/api`, and valid for eight
hours. Secure is enabled on HTTPS and hosted Vercel; local HTTP remains usable.
No demo credential is saved in localStorage or sessionStorage. DELETE
`/api/session` clears the browser cookie; saved work is retained. Sign-out clears
private frontend state and unsaved edits. Session expiry requires reconnecting.
This is shared-account demo authentication, not per-user sign-in. Sign-out does
not revoke an independently copied session cookie before its expiry.

Browser session endpoints and cookie-authenticated writes reject an explicit
cross-origin Origin header. These cookie flows use the same application origin;
separate-origin API clients can continue using bearer authentication. Explicit
invalid bearer credentials are rejected even if a session cookie is valid.
API responses, including errors and session responses, use `Cache-Control: no-store`.
Pages recheck state when restored from the browser's back/forward cache.

The dev console displays only persisted records and public health configuration.
Its snapshot-fetch timing measures the browser API request. Recorded run intervals
include lifecycle time (potentially user review), and are not provider latency.
Token usage, provider latency, and raw outbound provider requests are not recorded.

## Voice → reviewed transcript → conversation

`POST /api/voice/transcribe` accepts a raw `audio/wav` body with the same
authentication and same-origin session rules as other writes. It accepts mono
PCM16 WAV at 16 or 24 kHz, between 0.25 and 60 seconds, capped at 2,880,044 bytes.
The browser captures at 24 kHz through Web Audio. The backend bounds the request
stream, validates the WAV and duration, then calls Meta's `/asr/transcribe` in
`PUSH_TO_TALK` mode using the server's `META_API_KEY` and `META_VOICE_MODEL`
(default `muse-voice-transcribe-1.0`). Credentials remain server-side.

Success: `{"transcript":"Finish my homework.","model":"muse-voice-transcribe-1.0"}`.
Transcript text must be nonempty and at most 10,000 characters. Errors use the
standard error envelope: 401 unauthenticated; 403 cross-origin cookie write;
413 oversized recording; 415 wrong content type; 422 invalid audio or no speech;
502 provider connection/response failure; 503 missing configuration, unavailable
model access, or provider rate limiting. Provider bodies/credentials are not
exposed. The provider timeout is 45 seconds. Responses use `Cache-Control: no-store`.

This endpoint does not save audio, messages, runs, or tasks. Audio is held only
in memory while forwarded to Meta; no app-side disk or database retention occurs.
The browser sends audio only after **Stop & transcribe**. Cancel/navigation
release capture and discard browser audio; they cannot recall an upload already
sent to Meta. Failed requests retain browser audio for explicit retry until
cancelled, navigated away, another recording starts, or another action discards
it. Retries may make a new transcription call; this endpoint has no idempotency key.

The returned text populates an editable draft. The user explicitly sends it as
`message` to `POST /api/conversation`, using the existing `request_id` and optional
`review_draft`. Normal validation, retry, proposal review, and persistence rules
apply. Sent transcripts are ordinary user messages; modality is not recorded.
A combined typed draft and transcript longer than 10,000 characters must be
shortened before Send. Unsupported/insecure browsers retain text entry.

Verified API references: [Meta speech-to-text guide](https://dev.meta.ai/docs/speech-to-text)
and [official file-transcription client](https://github.com/meta-models/meta-model-cookbook/blob/main/06_muse_voice/01_voice_api_fundamentals/utils.py).
