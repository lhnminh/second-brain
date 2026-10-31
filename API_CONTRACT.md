# Backend API contract — first implementation

Status: implemented backend contract; the quick dashboard's core task/planning
flow has been verified locally in a browser. All paths are relative to the backend origin. JSON request and
response bodies use snake_case. Interactive schemas: `/docs`; machine schema:
`/openapi.json`.

**Current dashboard behavior (October 30):** Chat requests set
`apply_immediately: true` and save validated task objects directly. The review
flow below remains supported for legacy API clients that omit or disable this
flag. See “Direct task creation from conversation” for the current app flow.

## Identity and transport

The hackathon MVP uses one anonymous workspace per browser profile and app origin.
A server-generated 256-bit random HttpOnly cookie (`second_brain_workspace`)
selects the workspace. Its value is a private capability; the public `user_id`
is a one-way hash of that value and the configured `MOCK_USER_ID` namespace.
Neither a body field nor an identity header can select an owner. Every task,
context record, message, planning run, and event is scoped to the workspace.
`/` and `/dev` initialize the cookie before their parallel API requests.

The workspace cookie uses Path=/, SameSite=Lax (including returns from external
links), Secure on HTTPS/Vercel, and a one-year lifetime renewed on use. Sign-out
retains it. Clearing/expiring cookies, a different browser profile, private
browsing, or a different app origin starts a separate workspace; there is no
account recovery or cross-device linking. Copying the cookie transfers workspace
access. Existing shared-demo records remain stored but are not assigned to a
new browser. No database migration is needed.

If `MOCK_AUTH_TOKEN` is configured, data requests additionally require an
eight-hour browser access session or `Authorization: Bearer <demo token>`.
This shared access gate is not the Meta key and does not select a shared owner.
Bearer clients must retain workspace cookies in a cookie jar between requests
and initialize the jar before sending concurrent requests. Without a cookie,
authorized API requests create a fresh workspace. Local development without a
token uses the same browser isolation without the access gate.
Hosted Vercel instances still require the token and a Postgres URL.
Individual sign-in, recovery, and cross-device workspaces are roadmap work,
not hackathon requirements.

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

Optional `conversation_id` (UUID) scopes recent messages and run states sent to
Muse to that chat within the authenticated workspace. The dashboard generates it
in memory on each page load or login and renders only messages linked to that
chat's runs. Saved tasks/context and canvas reviews persist independently; the
full dashboard snapshot remains available for diagnostics. Omitting the ID keeps
legacy client behavior. Changing it when retrying a request returns 409.

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
not the access token. It is bound to the browser workspace and configured namespace, and signed with
the demo token. Missing/mismatched workspace cookies, namespace changes, or token
rotation invalidate access sessions. Token rotation preserves workspace identity;
reconnect with the new token to return to saved work.
The session works across serverless workers without an in-memory session store.

The cookie is HttpOnly, SameSite=Strict, scoped to `/api`, and valid for eight
hours. Secure is enabled on HTTPS and hosted Vercel; local HTTP remains usable.
No demo credential is saved in localStorage or sessionStorage. DELETE
`/api/session` clears only the access-session cookie; the workspace cookie and
saved work are retained. Sign-out clears
private frontend state and unsaved edits. Session expiry requires reconnecting.
This is anonymous browser ownership with a shared access gate. Individual sign-in
is on the roadmap. Sign-out does
not revoke an independently copied session cookie before its expiry.

Browser session endpoints and cookie-authenticated writes reject an explicit
cross-origin Origin header. These cookie flows use the same application origin;
Non-browser API clients can use bearer authentication with a persistent cookie jar. Explicit
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

## Hand off to Muse (October 30)

Pending tasks and steps classified for Muse expose one **Hand off to Muse** action. This is the entry
point for future work on a connected computer. No computer or worker is connected
yet. Clicking the button displays “No computer connected” and leaves task state
unchanged. It does not make an API/model request, queue work, or create a run.
The sample day exposes the same button and the same disconnected state.

The earlier task-drafting interface and draft-generation/save endpoints have
been removed following the user's correction. General chat continues to handle
planning, clarification, and reviewed task updates through existing endpoints.

Migration `753bc02ac941` remains in the schema history because it was already
applied. Its `task_drafts` table and any saved drafts are retained; no downgrade
or data deletion is performed. Dashboard `drafts` records and historical draft
runs remain available for diagnostics. Their presence does not mean a computer
handoff occurred. Old task-drafting messages are excluded from general chat.

Future integration must authenticate the machine/worker, transfer the selected
task context, and report actual execution status. A task must not appear running
until a real worker has accepted it. Computer connection, execution, screen
viewing, pause/resume, and human takeover are still unimplemented.

## Classify handoffs while creating tasks (October 30)

Migration `ae73dc160b52` adds nullable `tasks.handoff` (JSON) and
`tasks.handoff_source` (string). Existing tasks remain unassessed; no data is
backfilled, executed, or assigned automatically.

Every new Meta-generated task and subtask includes:

```json
{
  "handoff": {
    "handler": "muse",
    "reason": "Computer work that produces a reviewable document.",
    "requirements": ["Project notes", "Document editor access"],
    "done_when": "An agenda draft is ready for review."
  }
}
```

`handler` is `muse` or `user`. This is a suitability recommendation, independent
of task status, machine connectivity, access, or authorization. Mixed work should
be split at useful human/agent handoffs. Missing context/tools/access are explicit
requirements rather than proof the task must be done by a human. Required
human choices and physical work should remain human tasks.

`reason` is 1–1,000 characters; `done_when` is 1–2,000 characters; `requirements`
is an explicit list of zero to ten nonempty strings, each at most 500 characters.
The model adapter requires non-null classification on all newly created objects in
the same structured response that creates them. Missing, invalid, or incomplete
output fails without mutating tasks. Old stored proposals may omit the field and
remain reviewable; their tasks are unassessed.

Conversation approval persists the reviewed classifications on tasks/children.
Task-specific plan approval persists them on its new subtasks. An unchanged
model recommendation uses `handoff_source: model`; a classification edited in
review uses `user`. Direct task create/edit can also provide `handoff`, using
`user` provenance. PATCH uses the existing `expected_version` guard, audit
history, and owner checks. Null explicitly clears an assessment on direct edit.
Unrelated edits do not change classification provenance. New model suggestions
cannot override an existing classification with `handoff_source: user`.

The proposal review and direct task editor let the user inspect/correct handler,
reason, requirements, and completion criteria. The canvas shows **Hand off to
Muse** only for unfinished tasks with `handoff.handler: muse`. Human tasks show
**For you**; null/missing classifications show **Not assessed**. Requirements and
completion criteria are available under Handoff details. The click handler also
checks saved eligibility, so a human/unassessed task cannot be handed off through
a stale or manually triggered button. No worker is connected: eligible handoffs
still show the disconnected message and make no model/execution request.

The sample day has explicit fixture classifications, illustrating Muse work,
human work, and mixed plans. These examples do not represent a live classifier
run. General chat can propose classifications for saved, unassessed tasks via
normal reviewed conversation updates; old data is never silently reclassified.

### Completion response usage

PATCH `/api/tasks/{id}` returns the complete saved task after the transaction
commits. The canvas uses this response to update just that task and render the
next action without a full dashboard refresh. A **Saving…** indicator separates
immediate checkbox feedback from confirmed persistence. Conflict/failure does
not advance task state. The endpoint retains ownership, optimistic version
checks, account locking, workspace revision updates, and auditing; avoiding an
unused account-revision read and a second task read removes two SQL round trips.


## Direct task creation from conversation

POST `/api/conversation` adds optional strict boolean `apply_immediately`
(default false for API compatibility). The dashboard always sends true:

```json
{
  "request_id": "8a9883da-52c7-47d1-8715-5988f0958e1e",
  "conversation_id": "1ba280a7-de43-4676-8d6a-d676870a13ca",
  "message": "Prepare a team workshop with an agenda and a room measurement",
  "apply_immediately": true
}
```

The response remains a persisted run with validated task data in `proposal`.
That field name supports diagnostics and older clients; it does not mean the
objects are unsaved. A nonempty valid response is applied in the same final
transaction as audit events, the assistant message, and the `applied` run state.
There is no intermediate `awaiting_review` response or extra approval request.
Use `/api/dashboard` to read the resulting saved objects and their IDs.

A reply with no task updates ends as `answered`. A clearly identified task may
save while the reply asks for missing details; unsupported steps and deadlines
must not be invented. Generated new tasks and subtasks require valid handoff
classifications. User-cleared assessments on existing tasks remain preservable.
Model/data validation failure produces `failed` with saved tasks unchanged.
A workspace edit or newer overlapping conversation produces `stale`, applying
no changes. Transaction failure rolls back task writes, audit changes, and any
successful assistant reply together. External execution and completion status
are not affected by direct task saving.

Retries reuse the same request ID, message, conversation ID, and save mode; they
return the original run without duplicate tasks or another model call. Changing
mode with a used ID returns 409. Historical requests that omitted the new flag
are normalized to false when comparing retry identity. Unknown/invalid fields
continue to be rejected. API review endpoints and old pending proposals remain
supported; the canvas shows only compact recovery controls for those plans.
A successful new task response supersedes older pending conversation proposals
using the existing behavior, preventing later acceptance of obsolete versions.

Follow-up corrections reference the exact saved task ID. Unrelated fields,
existing steps, user importance choices, and user handoff corrections remain
protected. Version/revision checks prevent an in-flight model response from
overwriting a newer direct edit. Each automatic task change is audited.
No schema migration is required for this mode.

### Active work versus finished history

Model snapshots now place active work in `tasks` and historical work in
`completed_tasks`. A task is historical if it is explicitly completed, its
leaf steps are all completed, or it belongs beneath a finished parent. History
records include a model-context-only `completion_reason`: `completed`,
`all_steps_completed`, or `completed_parent`. Stored task status is not changed;
manual parent completion and the dashboard/API task records retain their
existing semantics. A partially completed plan with unfinished steps stays active.

A finished task with the same title must not suppress a new commitment. The
model must create a fresh task ID, preserving the historical record and not
inheriting its deadline, brief, steps, or completion state. Duplicate avoidance
applies to active commitments. Current state is authoritative over earlier chat
messages and old run proposals. Explicit historical record corrections remain
possible because output validation checks all owned saved tasks, not only the
active list. Generated subtasks cannot be appended to a historical parent;
new work belongs to a separate active task. No migration is needed.

### Preserve the outcome while clarifying details

Task titles name the user's intended outcome. Missing inputs are requested in
`reply`; they must not become the entire work breakdown. Unknown assessment
requirements can support a broad requirements/work/check scaffold, with exact
implementation details and ambiguous deadlines left unset. An existing active
clarification-only plan should be refined using its parent/step IDs and only
missing work appended. Existing unassessed task records may keep null handoff
data during an update; all newly created tasks and subtasks still require valid
classifications. User-cleared assessments remain protected.

The provider response allowance is 8,192 completion tokens for structured task
plans and multi-object repairs. Truncated or invalid responses remain failures
and are never partially saved. No schema or model-provider change is required.
