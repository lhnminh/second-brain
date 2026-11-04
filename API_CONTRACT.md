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

Pending tasks and steps classified for Muse expose **Ask Muse**. As of November 3,
this opens the existing persistent chat for the exact saved task/subtask ID via
`chat_task_id`. Opening it sends no request, creates no run, and does not change
task status. Repeated opens retain that scope's saved history and in-memory draft.
Sample tasks have no saved chat and show a preview-only notice. A future computer
handoff remains unimplemented; the browser reports execution as unavailable.

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
`reply`; they must not become invented work. The provider instructions default
to `subtasks=[]`. Generate children only when the current user explicitly requests
steps/a checklist/a breakdown or supplies steps to save. A task creation request,
complexity, or deadline alone is insufficient. Do not repair or expand existing
steps during unrelated edits. This supersedes the former automatic scaffold rule.
Explicitly requested corrections retain exact parent/step IDs; unknown details
and ambiguous deadlines remain unset. Existing unassessed task records may keep null handoff
data during an update; all newly created tasks and subtasks still require valid
classifications. User-cleared assessments remain protected.

The provider response allowance is 8,192 completion tokens for structured task
plans and multi-object repairs. Truncated or invalid responses remain failures
and are never partially saved. No schema or model-provider change is required.


## WebMCP browser action boundary

The dashboard exposes the existing authenticated contracts through same-origin
`document.modelContext` tools; no additional HTTP endpoints are introduced.

| Tool | Existing HTTP operation |
| --- | --- |
| `get_dashboard` | `GET /api/dashboard`; project saved tasks, handoff assessments, pending conversation proposals, and current-chat run summaries. Optional `request_id` selects a run across visits. Omit owner IDs and internal scores. |
| `create_task` | `POST /api/tasks`; optional `parent_task_id` creates a subtask. |
| `update_task` | `PATCH /api/tasks/{task_id}`; require `expected_version` and at least one editable field. |
| `send_muse_message` | `POST /api/conversation`; require message and caller request UUID, use `conversation_id: null`, the selected `chat_task_id`, and `apply_immediately: true`. |
| `resolve_pending_review` | `POST /api/conversation/{run_id}/approve` or `POST /api/runs/{run_id}/reject`. |

The three existing UI helpers (`draft_muse_message`, `open_task_editor`, and
`show_pending_reviews`) remain optional. Mutations return authoritative saved
records or actual run statuses, refresh the dashboard, and preserve unsaved user
edits. Server ownership, validation, audit, and revision rules remain authoritative.
Transport interruption returns `outcome: "unknown"` with verification guidance;
HTTP rejection returns `outcome: "rejected"` and status. A refresh failure after
a successful write returns `ui_warning` alongside the saved result. Creation has
no automatic idempotency: inspect saved state before retrying. Muse request UUIDs
retain the existing idempotency behavior for the same message and conversation.
No tool connects a machine or claims execution has started.

## Persistent task conversations (November 3)

`POST /api/conversation` accepts optional `chat_task_id` (owned task UUID or null).
It is a conversation scope, independent of the legacy planning run's `task_id`.
Ownership is checked before creating a run, saving a message, or calling Muse.
The request scope is part of retry identity: changing tasks with the same
`request_id` returns 409. Omitted fields in old stored requests normalize to null.

The dashboard sends `conversation_id: null` so general history persists rather
than starting a new visit. A non-null `chat_task_id` selects the root task's messages
and model context across visits, resolving descendant IDs to that root. Creation/correction runs are linked by task audit records; task-specific
answers also carry the validated proposal `chat_task_id`. Unrelated task
conversations are excluded. General chat excludes messages sent within a task-specific thread.
Legacy non-null `conversation_id` still scopes a general API conversation to a
visit. No database migration or authentication change is needed.

`GET /api/dashboard` adds `related_task_ids` to each run, derived from this
workspace's `task.created` / `task.edited` audit events. No title matching or
inferred associations are used. Full messages remain stored; only the latest
20 scoped messages enter a model request. The UI displays the full scoped history.

Accepted run proposals and redundant input payloads are excluded from recent-run
model context; saved tasks remain authoritative. New subtask records and their
individual audit events are bulk-inserted in the existing transaction, preserving
order, ownership, and rollback. Tests confirm the same SQL call count for one
and eight subtasks. Live provider/network latency has not been measured.


## Manual task creation and focus selection (November 3)

`POST /api/tasks` and `PATCH /api/tasks/{task_id}` accept optional
`time_horizon: "short_term" | "long_term" | null`. An explicit value pins a root
task to that focus section independently of deadlines or saved subtasks. Null
keeps the previous inference (dated tasks or saved plans on the left, remaining
undated tasks on the right). Existing records remain null; no tasks are moved
by the migration. Direct task creation saves only user-supplied task objects and makes no model call.

Apply migration `c42b193d7e61` before using the updated backend. Ownership, version
checks and audit records cover this field. Muse corrections preserve an existing
user selection; its proposal schema does not override this field.


**Reopening completed plans:** The dashboard uses a normal version-checked task
PATCH. Reopen sets `status="pending"` unless all leaf subtasks are completed;
then it sets `status="in_progress"`. It never unchecks children. Both dashboard
grouping and model-context projection keep such in-progress roots active even
when all saved steps are finished. Explicitly completed roots remain historical.
Past-task rows expose only this action, without changing stored chats or steps.


## Manual named-subtask plans (November 3)

`POST /api/tasks` also accepts optional `subtasks: [{"title": "..."}]` (maximum
20; each title 1–300 non-whitespace characters). This applies to root tasks only
in either focus section. Batches are rejected when `parent_task_id` is supplied. The root, children, and audit
records save in one transaction, with no model call or generated content.
When supplied, the response remains a saved root object and additionally includes
`subtasks`, containing the saved child records in entered order. Without children
the response is unchanged. Child deadlines/classifications are not invented.
Both forms allow zero entered steps. Adding to an existing task uses the normal
`POST /api/tasks` child creation endpoint with a title and `parent_task_id`. No new database migration.


## Root-task chat routing and focus corrections (November 3)

Conversation task objects now accept nullable `time_horizon` (`short_term` or
`long_term`). A non-null choice persists on new/existing tasks; omitted/null
values preserve an existing task's focus. Older saved proposals remain readable.
New Meta structured generations require the field, using null when unchanged.

`ConversationProposal` also accepts `chat_task_id` (owned saved task UUID or null).
This identifies an unambiguous task discussion, including answers with no edits.
Unavailable/foreign IDs fail validation before any changes or assistant success
message are saved. The frontend uses this ID, a unique newly created root, or a
unique affected root to select the matching persistent chat after success.
Ambiguous multiple-task responses keep the current selection.

Subtask chat requests resolve to their owned root for model context. Historical
runs retain their original input payloads and request identities; root histories
include descendant scopes and linked changes. No messages are deleted or moved.
The browser selector lists roots only, and subtask Ask Muse opens its root.

The simplified task editor PATCHes only focus, importance and a changed handoff
assessment. It retains the existing structured handoff context; a fresh manual
assignment records `reason: "Assigned by you."`, empty requirements and the task
name as the completion criterion. Status, title, description and deadline remain
available through direct dashboard controls. No database migration is needed.


### Exclusive chat ownership correction

Dashboard runs now include computed `chat_scope_id` (an owned root task UUID or
null for General chat). Each exchange has exactly one destination: after a
successful reply, prefer the validated proposal `chat_task_id`, then a unique
created root, then a unique affected root, otherwise retain the original scope.
Unsuccessful/running exchanges stay in the original scope. Subtasks resolve to
their root. The UI, WebMCP current-chat reads and model-history snapshots all use
that same destination. Raw messages and original `input_payload` remain stored
once; request identity is unchanged, so older routed exchanges are corrected on
reload without deleting messages or migrating the database. `related_task_ids`
remains audit information, not additional copies of the chat.

A delivered message clears its matching draft/pending request before UI refresh.
A later rendering/refresh error must not restore already-sent text. Genuine
network uncertainty still preserves the draft and request UUID. WebMCP retries
reuse the original request scope even after automatic selection moves to a task.


## Name-only task interface

Tasks and subtasks use editable titles and optional deadlines; descriptions no
longer have dashboard, creation-form or bubble controls. Description columns and
API fields remain compatible, and existing stored context is preserved. New model
descriptions default to empty; supporting context belongs in the task chat.

Both manual root forms accept optional named subtasks (maximum 20 per batch).
Existing tasks expose Add subtask with one required name, saving a pending child
without a model call, generated metadata or an inherited deadline. For an older
root with null `time_horizon`, the frontend first pins its current effective focus
using version-checked PATCH, then creates the child. A failure preserves the form;
a successful pin alone does not move the task's visible section. No migration.


## Background subtask suitability assessment (November 3)

`POST /api/handoff/assess` requires the normal workspace session:

```json
{"request_id":"UUID", "task_ids":["saved-subtask-UUID"]}
```

Supply 1–20 unique owned subtasks with one shared parent. Roots and duplicate IDs
return 422; foreign/unavailable tasks return 404; user-assigned classifications
are protected with 409. Reusing a request UUID with different input returns 409.
The configured Meta model receives the saved parent/step context and a strict
assessment schema. Output must classify exactly the requested IDs once each.

Responses include `id`, `request_id`, `status`, `error`, and `tasks` (the current
saved requested records). Status is `running`, `answered`, `failed`, or `stale`.
Successful assessments atomically update only `handoff`, `handoff_source=model`,
version and timestamps, with audit events and a diagnostic run. Parent/child
version changes during inference make the run stale without overwriting edits.
Invalid/provider output leaves the saved steps intact. Repeating the same UUID
returns the existing run without repeating the model call. No chat messages are
created, no task is marked running/completed, and no computer work is executed.

The browser saves manually entered steps first, then calls this endpoint in the
background. Chat-created steps already have validated classifications. Failed
assessments can be retried separately from task creation. Sample workspace mode
is removed. The task editor now PATCHes only focus and importance, preserving
existing handoff metadata. Blue Ask Muse opens root chat; per-subtask Hand off
opens a no-computer-connected notice until an execution worker is implemented.


## Dedicated laptop browser (November 3)

Migration `d785c418a901` adds owned `browser_runs`, separate from planning runs
and chat messages. All routes use normal workspace identity. Start, run reads,
controls and artifacts additionally require a loopback client and localhost host,
reject foreign Origin headers, and reject hosted execution. The local app must
run with its optional browser worker enabled and one process.

| Route | Result |
| --- | --- |
| `GET /api/browser` | `connected`, `mode`, setup `reason`, latest 30 owned `runs`; hosted returns disconnected with no runs |
| `POST /api/browser/runs` | 202 with saved run; requires UUID `request_id`, owned leaf `task_id`, current `expected_version`, public `start_url`, optional `instructions` <=2000 chars |
| `GET /api/browser/runs/{id}` | Owned persisted status/result |
| `POST /api/browser/runs/{id}/control` | `{action: pause/resume/stop}`; Resume only from paused/needs_input |
| `GET /api/browser/runs/{id}/frames/{frame}` | Owned saved PNG, no-store |
| `GET /api/browser/runs/{id}/downloads/{file_id}` | Owned attachment; original sanitized display name, opaque local storage filename |

Run responses contain id, task_id, task_title (the title at start), request_id, start_url, status, summary, steps,
downloads, frame, created_at and updated_at. Goal snapshots/owner IDs are not
returned. Statuses: queued, running, pausing, paused, needs_input, stopping, stopped,
interrupted, failed, finished. Finished means the worker ended for user review,
including a step-limit exit; it never marks a task complete.

Duplicate request UUIDs with identical payload return the same run, without
repeating execution; changed payload gives 409. Unavailable worker gives 503,
foreign work 404, stale versions/ineligible or completed work/capacity conflicts
409, invalid URLs or non-leaf targets 422. A run requires unfinished Muse-suitable
work beneath unfinished ancestors. Task/ancestor version changes interrupt further
actions. Browser state changes never mutate task status or insert chat messages.

One local thread owns each browser, with one active browser per app process. The
worker saves screenshots/actions/downloads after action batches. Pause/Stop wait
for an in-flight action/model request before the next action; Resume discards
stale actions and starts from a fresh screenshot. Shutdown requests stop; a new
worker marks abandoned active records interrupted. Use one process and one local
worker per database. There is no hosted pairing protocol or cloud worker.

Screenshots/task context go to the existing Meta model via `/responses` with
`store:false`, strict validated function tools and serial calls. The native tool
was rejected in the account's smoke check; it is not silently retried. URLs are
checked against public HTTP/HTTPS and standard ports, including DNS results on
browser requests; this is a browser guard rather than network/VM isolation.


## Internet chat, stable surfaces and reversible removal (November 4)

Current dashboard/WebMCP conversations send `web_enabled: true` and
`keep_chat_scope: true`. Both fields default false for legacy clients. General
requests retain null chat_task_id even when creating/discussing one task; task
requests retain their owned root scope. Older stored request payloads and retry
identities remain valid through default normalization. No history is rewritten.

Optional `delegated_task_id` identifies the specific task/subtask handed off. It
must be active, owned, and in the supplied root task chat; wrong chat scope gives
422, foreign work 404 and finished work 409. The snapshot includes that saved
object plus the root/current task context. This invokes internet-enabled chat,
not browser execution, and never changes task completion status automatically.

Internet answers use Meta `/responses` with built-in `web_search`, store:false and
a strict ConversationProposal schema. Progress messages can precede the final
structured message; only the last message is parsed as the proposal. All task
changes still pass normal ownership, score, revision and user-correction checks
before atomic application. `proposal.web_search_used` and `proposal.sources`
({url,title}, max 10) are derived from actual completed search calls and URL
citation annotations, overriding any generated values. A valid answer may use no
search; the interface must not claim otherwise. Legacy no-web calls clear this
metadata. Failures preserve work and are visible inside the current chat surface.

### Task trash and Undo

Migration `e490ac621fb8` adds nullable tasks.deleted_at. These endpoints use normal
workspace authentication and same-origin checks:

- `DELETE /api/tasks/{id}` with `{request_id: UUID, expected_version: integer}`
  removes that active task and its active descendants from dashboard/model state.
  Returns `{deletion_id, task_ids}`. All affected rows receive one deletion stamp
  and version increment in a transaction, with an audit record and revision bump.
- `POST /api/tasks/{id}/restore` with `{deletion_id: UUID}` restores that exact
  deletion group, using the same IDs and saved fields. A deleted parent must be
  restored first. Independently deleted children are not resurrected with a later
  parent deletion. Repeated restoration is safe; an older token cannot undo a
  later deletion of the same task.

Duplicate deletion request IDs with identical input return the same result; a
changed input or stale version gives 409. Cross-owner actions give 404. There is
no physical row deletion, chat deletion, artifact deletion or purge endpoint.
Normal task reads/edits/add-child operations exclude removed tasks. Dashboard runs
retain their original root chat_scope_id and mark `chat_hidden` for a removed root,
so preserved task exchanges do not appear in General or its model context. Undo
restores visibility. Raw owner-scoped diagnostic history is retained.

### Optional whole-task browser runs

Only an explicit browser start endpoint launches a computer. It now accepts an
unfinished whole task, with saved descendant context, as well as a Muse-suitable
subtask. Whole-task execution remains limited to the available browser; human
steps are not authorized automatically. Captured task/ancestor/descendant versions
and the current descendant set are checked before actions; corrections, removal
or newly added delegated steps interrupt execution. Results remain separate from
completion status and are rendered in the root's task chat.

Relevant earlier user statements that created or clearly discussed a task in
another chat are supplied as bounded task_user_context in model snapshots. Current
saved state and later corrections take precedence. Visible exchanges remain in
their original General/task surface, without copied messages or unrelated general
context. Uncertain subtask handoff retries retain the original delegated ID.

November 4 verification: all 224 automated tests pass. Isolated real-Muse browser
checks verified contextual creation of three grounded steps, official-source web
research, a whole-task handoff in the existing task chat, separate General history
and drafts, optional browser setup, deletion/Undo for both focus sections and a
subtask, and restored task chat after Undo/reload. Desktop, 390×844 and 1226×540
checks found no outer chat overflow, including the expanded voice note. The
configured migration preserved existing task/chat/context/audit/browser-run counts.


November 4 refinement: new delegated chat/browser requests require short-term
work. Whole-task handoff requires every leaf step to be assessed for Muse;
a task with no steps requires its own Muse assessment. Long-term tasks keep
planning chat and saved results, without handoff controls. The backend rejects
ineligible new requests with 409. Chat replies hide native citation reference
codes and retain real source links; the provider is instructed to use readable
Markdown. Focus headers omit counts, composers are compact, and the long-term
list scrolls only after reaching the adjacent short-term panel's height.
