# Conversation canvas and development workspace

## Follow-up polish (November 3)

Section counts include **task/tasks**. Bubble details open their subtask list
immediately, while overview task lists remain collapsed by default. Each saved
deadline appears with its own task/subtask; the parent deadline is not copied to
undated children. Dated bubbles also show their deadline. The long-term workspace
summary and the icon beside **Muse** are removed. Chat, history, description
panels, and textareas allow scroll chaining instead of trapping the wheel at an
inner scroll boundary.

Targeted frontend/chat/voice checks passed. Browser checks verified counts,
auto-opened bubble steps, the removed elements, and wheel scrolling over the chat
composer through the chat panel into the page. No live model call was made.

## Task conversations and simpler task lists (November 3, 2026)

This supersedes the earlier visit-reset chat behavior and next-action display.
**Task chat** opens a task's persistent conversation; the conversation selector
also includes subtasks and **All tasks**. Histories are server-stored in the
current browser workspace and survive reload/sign-out. The selected scope is
remembered per workspace, and unsent drafts/retry IDs stay separate while
switching scopes in the current page. Unsent drafts do not survive reload.
**Ctrl+Enter** or **Cmd+Enter** sends; Enter alone keeps multiline input.

Each task has one **Subtasks** disclosure, initially closed. It contains the
complete ordered leaf-step list with completed steps struck through. The progress
fraction counts that exact list, excluding the parent. Open lists survive in-page
refresh/completion. Bubble details scroll into view on selection, switching, and
expansion; the panel scrolls internally when taller than the viewport. The date
is the main heading. The logo, decorative arrows, duplicated deadline/sample
labels, separate completed-step disclosure, and importance-size caption are removed.

Verification: 152 tests pass using
`uv run python backend/tests/run_windows_checks.py backend/tests -q`. This
Windows-safe launcher uses Node script files and short audio-fixture parameter IDs. Tests cover persistent scoped history,
ownership, retry scope, bulk-write rollback/order and SQL-call count, Ctrl+Enter,
exact displayed step counts, and existing voice/browser tools. Browser checks verified ordered lists, bubble switching/expansion visibility,
Ctrl+Enter submission, separate task conversations, and history/selected-scope
persistence after reload. Chat checks used a separate disposable database with
explicitly labeled fixture replies; they do not verify live Muse response latency.

## Quiet workspace refresh (November 3, 2026)

The dashboard retains focus on the left, undated long-term tasks on the right,
and task bubbles below. The refresh uses a light neutral palette, larger system
type, fewer labels, a single next step per task, and a **View plan** disclosure.
Long-term rows open the same details as bubbles. **Ask Muse** retains the existing
disconnected-computer message; it does not start work. The header's **Workspace**
menu groups refresh, diagnostics, and sign-out. A labeled **Talk to Muse** button
opens the existing chat and voice controls. See [DESIGN.md](DESIGN.md) for tokens
and interaction rules. No API, storage, model configuration, or dependencies change.

Verification: 17 targeted existing tests pass. On Windows, three Node harnesses
exceed the command-line length limit when passed with `node -e`; running their
unchanged scripts from temporary files lets the same checks run successfully.
Browser checks covered sample completion, plan disclosures, long-term details,
the empty workspace, chat, and a 390px mobile viewport without horizontal overflow.
No live model or microphone calls were made for this visual refresh.

### Visual direction (October 31)

The dashboard uses a warm paper background, dark ink, a lime workspace summary,
and peach, yellow, sage, teal, and lavender task bubbles. Priority titles are
25–34px on desktop and 28px on narrow screens; bubble titles are 18–29px on
desktop. System fonts and Georgia keep the design independent of external assets.
Repeated section captions and chat instructions are removed. Each priority still
shows its next action, with remaining steps, notes, and task controls expandable.
“The big picture” summarizes open tasks, the nearest unfinished deadline, and
step progress from saved records. Plans with every step checked off remain open
until explicitly completed. Empty and fully completed workspaces have distinct
summaries. This uses no model call; importance levels, saved state, and the API
are unchanged.

Browser review used the isolated sample day in the existing local app: completion
advanced the next action and progress, and selecting a bubble opened its details.
Sample actions do not change saved tasks. Mobile styling is implemented but has
not been visually checked on a narrow viewport.

The workspace lives in `dashboard.py` and the developer console in `dev.py`,
following the repository's `.py` source convention. FastAPI serves the canvas at `/` and development tools at
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

1. Open Muse from the corner launcher and describe concrete work.
2. Muse identifies the task and useful steps, classifies who can handle each,
   and saves the validated objects directly to the dashboard.
3. If essential details are missing, answer a focused question in chat. A clearly
   identified task can already appear with unknown details left unset.
4. Edit a saved task or step, adjust importance or handoff suitability, or send a
   follow-up correction. Follow-ups target saved task IDs rather than new drafts.
5. Mark work complete and return later to saved state and persistent task chats.

New chat requests use `apply_immediately: true`. There is no proposal editor or
**Save reviewed plan** step. Validated changes and their audit events commit
atomically before the response returns. A failed or stale response changes no
tasks. Network retries retain the original message and request ID so a reply
lost after a successful save cannot create duplicate tasks.

Earlier unsaved plans remain as compact recovery cards with **Add these tasks**
and **Dismiss**. The legacy review API remains available. These cards do not
contain the previous large editing form; tasks can be edited after adding them.
The UI uses fixed task components; the model does not generate HTML or widgets.

## Development tools

`/dev` is a read-only diagnostic console rather than a second task-editing UI:

- Snapshot counts, configured model, account, access mode, and service liveness.
- Filterable model runs with actual input, review drafts, proposals, errors,
  timestamps, related messages, and linked events.
- Searchable saved tasks, context, and messages, with field and JSON inspectors.
- Searchable change history and the full account snapshot.
- Manual refresh and optional ten-second refresh while the page is visible.

New task updates save directly on the workspace; earlier unsaved plans remain recoverable there. The console labels pending changes,
stale data after a connection failure, and the limits of health/timing information.
Snapshot fetch timing is measured in the browser; provider latency and token usage
are not recorded. There are no task/context mutation controls in the dev console;
existing backend editing endpoints remain accessible through the API reference.

There are no seeded objects or simulated model responses in either page. The
Meta key stays server-side. The demo token is exchanged for an eight-hour signed HttpOnly session cookie;
it is not saved in JavaScript storage. A separate HttpOnly cookie selects this browser’s workspace for one year, renewed
on use. Clearing cookies, private browsing, or another browser starts a separate
workspace. Individual sign-in and cross-device access are roadmap work.
Both pages share the session and clear
private rendered state when access expires. Sign-out also discards unsaved edits. Browser drafts
survive in-page request failures, but unsaved edits are not persisted across
navigation or reload. A network retry reuses its request ID and input. Automatic onboarding extraction, real sign-in, arbitrary widgets, and task
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

October 27, 2026 refinement: session tests cover page navigation/reload, expiry,
tampering, token rotation, owner binding, HTTPS cookie flags, explicit cross-origin
write rejection, and sign-out. Desktop Safari checks verified the stable empty
layout and workspace → dev → workspace navigation without reconnecting.
Browser checks also traced a real Muse proposal through the console, recorded input,
approval, saved task objects, and linked events. Reload remained authenticated;
sign-out cleared private state and browser Back required login again. These checks
used an isolated local SQLite database, not deployed Neon.

## Voice input

Choose the **microphone icon**, allow microphone access, record up to one minute,
then choose the **stop icon** (labelled **Stop & transcribe**). Meta Voice Transcribe returns text into the composer.
Review/edit it and choose **Send** to use the existing Muse conversation and
conversation flow. After you send the reviewed transcript, validated task updates save directly.

Capture uses `getUserMedia` and an AudioWorklet, with mono PCM16 WAV encoding at
24 kHz. It requires HTTPS or localhost and microphone/Web Audio support. It does
not depend on the browser's speech recognition service, which failed in Dia.
At the one-minute limit, capture stops and waits for your transcription action.
Hiding/leaving the page, cancellation, and sign-out release recording resources.
Typing stays available when microphone capture is unavailable or denied.

**Stop & transcribe** sends audio through the authenticated backend to Meta's
`muse-voice-transcribe-1.0`, using the server's existing `META_API_KEY`.
`META_VOICE_MODEL` can override that model; `META_MODEL` still selects the separate
conversation/planning model. Restart the backend after adding the new route.

This app keeps audio only in memory, never in the database or on disk. A failed
transcription preserves your typed draft and offers **Retry transcription** using
the in-memory recording. **Cancel**, navigation, sign-out, sending a text message,
or beginning another recording discards that recording. Audio already submitted
to Meta cannot be recalled by Cancel. The composer discloses the audio transfer
before recording. Only explicitly sent text persists as a conversation message;
unsent transcripts do not survive reload. Spoken replies remain out of scope.

Automated tests cover the real controller with simulated microphone/network
interfaces, WAV encoding, permission failures, cancellation, late microphone
permission, timeout/retry, navigation cleanup, and reviewed text submission.
Backend tests cover audio validation, size/duration bounds, authentication,
cross-origin rejection, provider contracts/errors, and transcription without
saving records or invoking planning. Node is required for the controller test.
A computer-generated homework recording was transcribed successfully through the
real Meta adapter. The user confirmed the revised flow works in Dia on localhost.
Hosted deployment has not been verified for voice input.

## Layout polish (October 28, 2026)

The workspace uses a warm paper palette and a wider task canvas. Empty workspaces
keep the same layout and show first-use guidance; this is interface copy, not a
generated Muse reply. Saved cards show task status and
progress from completed immediate steps. Step progress does not automatically
complete the parent. Muse is now a floating panel, as described below.

Existing frontend and voice-controller tests pass. Render checks with DOM test
doubles covered empty, saved, review, escaped titles, preserved review edits, and
cleared state. These are simulated DOM checks, not visual browser verification.
Later Safari desktop checks are recorded below; mobile visual review remains
pending. This pass does not add or reverify a live model integration.

## Expandable Muse chat (October 28, 2026)

At the user's request, the previous fixed canvas-left/chat-right arrangement is
replaced by a full-width canvas and a circular Muse launcher at the bottom right.
Chat starts collapsed. The launcher and canvas conversation buttons open a floating
panel with a short fade/scale transition; reduced-motion preferences disable it.
The close button, launcher, or Escape collapse it. Hidden chat is inert so its
controls cannot receive keyboard focus; closing returns focus to the launcher.
The open/close controls remain available during a model request.

Closing preserves messages and typed drafts in the existing page DOM, and cancels
active voice capture/transcription so the microphone does not keep running out of
view. Drafts still do not persist across page reload. Reviews remain on the canvas;
following the panel's review link closes chat to reveal them. On small screens the
panel fits the viewport and scrolls internally when needed. No API changes or
additional frontend dependencies are required.

Safari desktop checks verified the collapsed launcher, expanded appearance, close
button, Escape/focus return, and unsent draft preservation across reopening. These
checks used the signed-out interface and did not call the model or microphone.
Mobile visual verification remains pending. Existing automated frontend and voice
checks also pass with simulated interfaces.

The composer uses a compact rounded input, a circular send arrow, and a microphone
icon. Recording replaces the microphone with a stop icon; setup/transcription
show a spinner. Voice controls retain accessible labels and hover titles. The
Meta transcription disclosure expands below the input.

## WebMCP browser tools

The workspace registers eight tools through `document.modelContext.registerTool()`.
An agent can read, create, rename, complete/reopen, and verify saved tasks, send
Muse messages, and resolve legacy plans without clicking browser controls.
The browser must already be connected to its workspace through the demo access gate.

| Tool | Behavior |
| --- | --- |
| `get_dashboard` | Read saved tasks, versions, handoff assessments, pending plan contents, current-chat run statuses, and execution availability. Optional `request_id` looks up a specific Muse run across page reloads. |
| `create_task` | Persist a task; optional `parent_task_id` creates a subtask. Return its ID and version. |
| `update_task` | Persist supplied fields using `task_id` and `expected_version`: title, description, deadline, importance, status, or handoff assessment. |
| `send_muse_message` | Send a message with a caller-provided `request_id` UUID, invoke the configured Muse adapter, and save validated task updates directly. Return actual run status and reply. |
| `resolve_pending_review` | Apply or dismiss an earlier unsaved conversation plan using `run_id` and `decision` (`apply` or `dismiss`). |
| `draft_muse_message` | Optionally stage visible text without sending. `send_muse_message` can send matching composer text. |
| `open_task_editor` | Optionally open the visible editor. Agents can save changes directly with `update_task`. |
| `show_pending_reviews` | Optionally bring earlier unsaved plans into view. Agents can resolve them directly with `resolve_pending_review`. |

Mutations use the existing same-origin, authenticated backend endpoints and server
ownership, validation, revision, and audit rules. No new backend contract or
provider is introduced. Results omit owner IDs and internal importance scores.
`user_importance_level` is the explicit user choice and can be unset.

Tools preserve unsaved inline names, open editors, and differing composer text.
Mutations refuse sample preview, concurrent requests, or voice capture. A model
failure or stale run returns its actual status. A transport failure after sending
returns `outcome: "unknown"`, because the server may have saved the request.
Read the dashboard before retrying task creation to avoid duplicates. A task
update conflict returns HTTP status 409: read the current version before revising.

For uncertain Muse requests, call `get_dashboard` with that `request_id` to check
its saved run. Retrying the same UUID and message in the same page visit reuses the
backend run. After a reload, inspect that run before sending new work; the fresh
visit has a different conversation ID. Terminal `failed` or `stale` requests need
a new UUID for a revised request. A failed UI refresh after a successful mutation
returns the saved result plus `ui_warning`; it does not turn a saved write into a
claimed failure. The tools do not implement machine execution: dashboard reads
explicitly report `execution.connected: false`.

For local setup:

1. Start the app using the commands above and open `http://localhost:8000/`.
2. In a compatible Chrome build, enable `chrome://flags/#enable-webmcp-testing`
   and relaunch, following [Chrome's WebMCP instructions](https://developer.chrome.com/docs/ai/webmcp).
3. Connect using the normal demo access form if prompted.
4. Check `typeof document.modelContext?.registerTool` in DevTools; expect
   `"function"`. Use a WebMCP-capable agent or Chrome's tool inspector to discover
   the eight tools.
5. Ask the agent to call `get_dashboard`, create a task and subtask, rename the
   task with `update_task`, and mark the subtask complete using its saved version.
   Call `get_dashboard` again, reload, and read once more to verify persistence.
6. Call `send_muse_message` with a fresh UUID and a planning request. Inspect its
   returned status/reply and use `get_dashboard` to verify actual saved updates.
   New messages save directly; no review click is required.

Registration requires HTTPS or localhost and the `document.modelContext` API.
Browsers exposing only the older `navigator.modelContext` API are unsupported.
Tools unregister on page exit and register again on back/forward restoration.
No polyfill, remote MCP server, or cross-origin tool exposure is added. This does
not configure the agent client or enroll the deployed origin in Chrome's trial.

Verification: `test_webmcp.py` simulates browser registration, reads, validation,
unsupported browsers, cancellation, and lifecycle cleanup. `test_webmcp_actions.py`
executes the shipped tools through a fetch bridge against FastAPI and SQLite with
real cookie authentication. It verifies task/subtask creation, rename, completion
and reopening, ownership isolation, stale versions, legacy plan apply/dismiss,
model-run retries, model failure, reload persistence, draft protection, concurrent
request blocking, uncertain write responses, and refresh failures. Browser APIs
and Muse responses are simulated. Native Chrome discovery and a deployed agent
journey remain unverified.

## Current dashboard (November 3, 2026)

- **Short-term focus:** roots explicitly selected as short-term. Unselected tasks
  with a deadline or saved leaf subtasks also appear here.
  Sort by earliest deadline, then importance; undated plans come last. Each task
  has one closed disclosure with all saved leaf steps, in order, including completed
  steps with a strike-through. Creating a task alone must not generate steps.
- **Long-term focus:** roots explicitly selected as long-term, plus remaining
  unselected active undated roots without subtasks. Compact
  descriptions open via a separate chevron on the right; names only edit. All entries share one scrollable list,
  without a separate “Show more” disclosure. The two focus sections do not overlap.
- **Everything on your mind:** draggable importance bubbles for all active roots.
  Selecting or switching bubbles keeps the current page position and bubble focus. Subtasks or the description are
  immediately visible and cannot be collapsed inside the detail panel.
- **Past tasks:** a separate section below the bubble map retains completed work.
  Rows are grouped into **Short-term** and **Long-term**, retaining their saved
  section choice (or legacy inference). Every row has a read-only name/status
  and only **Reopen task**. Roots with all
  leaf steps finished are labeled accordingly, without silently completing the
  parent. Reopening preserves done steps; fully checked plans return as in-progress
  until explicitly completed again. Saved chats become accessible from active work.

Each task/subtask displays its own deadline when saved. Date badges use red for overdue or due within one day, orange for two to
three days, yellow for four to seven days, and green for more than a week.
The sample label sits in the header; Workspace and the voice note use aligned
chevrons that turn on expansion. **Complete task** remains
last at the right of each action group, including when **Ask Muse** is available.
Chat close and microphone controls use the current neutral/blue palette.

**Ask Muse** opens the existing persistent chat for the exact saved task or subtask.
It sends no message, creates no run, and starts no machine execution. History stays
saved across visits and unsent drafts stay separate while switching scopes.
Sample tasks cannot open saved task chats. API credits and computer integration
are deferred; no real model calls were used to verify this refinement.

Open `http://127.0.0.1:8000/?draft=1` for a visibly labeled sample day. Samples never
replace saved workspace state or enter model context; their completions reset on
reload. All dashboard surfaces retain keyboard focus, reduced motion, and scroll
chaining through textboxes. Ctrl+Enter/Cmd+Enter sends chat; Enter adds a line.

**+ Add task** sits before each section count. Short-term creation asks for a task
name and numbered subtasks, with **+ Add subtask** and removal controls; at least
one entered step is required. It has no description field. Long-term creation
keeps an optional description and has no subtask rows. Both offer optional date
and importance. The short-term root and all entered steps save atomically in one
request; invalid or failed writes leave no partial plan. No Muse call or generated
steps are involved. Existing saved notes are preserved.

A saved `time_horizon` keeps the task in its chosen section. Edit task → Focus
section can change this or select Automatic for legacy inference. Apply migration
`c42b193d7e61` on a new checkout; no additional migration is required for these
form, toggle and archive refinements.

Task/subtask names and descriptions are inline fields; date badges open editable
dates. Enter/blur saves names, Ctrl/Cmd+Enter or blur saves descriptions, and Escape
cancels the edit. Names do not toggle long-term descriptions; use the dedicated
chevron, which announces its expanded state. Counts and interface labels remain
derived/static. Sample edits and added tasks reset on reload. The header tagline
has been removed.

Verification: 164 checks passed, including exact entered-step persistence/order,
invalid-list rejection and rollback of parents/children after an audit failure.
Browser checks with disposable SQLite verified adding/removing rows, saving and
reloading short-term plans, description-only long-term creation, independent title
editing and chevron toggling, and classified past tasks with only Reopen controls.
No real Muse calls were made.

The following notes record earlier implementation iterations; the behavior above
supersedes earlier descriptions of overlapping focus panels, automatic scaffolds,
“Show more,” collapsible bubble subtasks, and the disconnected handoff notice.

The bubble refinement removes the rectangular backlog cards and five-bar marks.
Bubbles begin in deterministic scattered positions, with smaller sizes on narrow
screens. They can be dragged and released with momentum. Collisions push other
bubbles and the field edges bounce them back; damping lets them settle. Dragging
does not change importance, tasks, or their saved order. Positions survive in-page
selection, rerenders, and window resizing, in separate sample/live coordinate
maps. Coordinates are not persisted across page reloads. Full titles
remain available to assistive technology and on hover; longer visible names are
limited to three lines. Completed bubbles disappear and close their selected
details. All 8 existing checks pass; a temporary DOM harness also verified bubble
counts, importance classes, selection/closing, completed removal, escaping, and
unassessed labels. Visual review remains with the user.


The scattered layout uses task IDs to seed placement, circle collision checks to
keep labels separate, and a growing field for larger backlogs. Importance controls
size rather than alignment. A temporary geometry harness checked repeatability,
bounds, separation, and irregular heights for 1–100 tasks across 220–1800px field
widths. All 8 existing frontend-related checks pass. Visual review remains with
the user.


Bubble interaction supports mouse/touch pointer capture, a five-pixel drag
threshold, and arrow-key nudging. Ordinary clicks and Enter still open details;
the click following a drag is suppressed. Canceling a pointer releases capture.
Reduced-motion preferences retain direct movement and collision separation while
skipping inertia. Animation frames stop after settling and are canceled on page
hide, navigation, or rerender. No new dependencies or backend contracts are used.

Verification: all 8 existing frontend-related checks pass. A temporary Node
harness executed the shipped physics/controller with simulated pointer events,
DOM, animation frames, and time. It verified dragging, neighbor collisions,
release momentum, bounds, settling, click/drag distinction, keyboard nudging,
reduced motion, cancellation, in-page position restoration, and cleanup. Visual
feel remains for the user's review.


Long-term focus is now connected to existing undated tasks, following the user's
clarification; no separate goal schema or integration is needed. Dated tasks are
excluded, and the panel shares the active-task completion filter. Changing a
saved deadline moves a task into or out of this view on refresh. Sample data uses
the same rule. The 8 existing frontend-related checks pass; a temporary harness
verified deadline filtering, detail targets, empty/overflow states, and escaping.

Expanding/collapsing task details, notes, completed work, and the long-term
"more" disclosure now uses a short height transition. Selecting a bubble reveals
its detail panel with opacity-only motion, without scrolling or moving focus. Repeated clicks can reverse a
running disclosure transition; reduced motion skips these effects. Existing
native disclosure/keyboard controls remain in use. All 8 existing checks pass;
a temporary animation harness verified expand/collapse, rapid reversal, style
cleanup, reduced motion, and bubble-detail reveal.

## Hand off to Muse (October 30, 2026)

Pending tasks and steps classified for Muse offer one **Hand off to Muse** button, including in
**Preview sample day**. The intended destination is a computer controlled by
Muse. A machine has not been connected yet, so clicking the button displays:
“No computer connected. Connect a computer to let Muse work on [task]. Nothing
has been started.” The message receives focus and is scrolled into view.

This setup state makes no network or model calls, creates no run, and does not
change task status or chat contents. Completed work has no handoff button.
The earlier drafting controls, task-drafting chat mode, and draft editor have
been removed. The existing planning conversation and voice input remain.

To check the interaction, choose **Preview sample day**, click a task's
**Hand off to Muse** button, and verify the disconnected message and unchanged
task. The same behavior applies to saved tasks. A real machine handoff cannot
be tested until the computer/worker is connected.

The already-applied draft-storage migration and any saved data are retained.
Apply normal migrations on a new checkout; no downgrade is needed.

### Handoff classification

The planning response now classifies tasks and steps as part of creating them.
Review **Muse can handle this**, **For you**, or **Not assessed**, expanding the
assessment to edit its handler, reason, requirements, and “Done when” result.
Once saved, the task editor supports the same corrections. Only work classified
for Muse offers **Hand off to Muse**. Computer connectivity remains a separate
setup state; no execution is performed.

The sample day includes fixture classifications: dashboard work and gathering
references can be handed off; walking, measuring a room, and personal choices
need you. Parent plans containing human work stay with you while individual
Muse steps offer handoff. Sample interactions never write to the backend.

Existing saved tasks initially show **Not assessed**. Edit an assessment directly
or ask general chat to assess saved tasks and review the proposed updates. Apply
migration `ae73dc160b52` before running the updated backend. User corrections
persist across visits and take precedence over later model suggestions.


Verification: 113 automated checks pass, including classification persistence,
review/direct corrections, invalid-output rejection, user isolation, legacy
migration/proposal compatibility, and conditional handoff rendering. A real Meta
request with synthetic workshop tasks produced both Muse and human subtasks;
a saved correction survived a fresh app instance with tasks still pending.
Migration `ae73dc160b52` was applied to the configured database after explicit
user approval, and the running localhost app serves the updated controls/API.
Existing task records remain readable. Browser visual QA remains pending.

### Workspace completion feedback (October 30)

Live task completion now checks the box immediately and shows **Saving…** while
the PATCH is pending. The saved task returned by the backend updates local task
state; the next action appears after confirmation and the existing completion
animation. Failure restores the prior checkbox and shows an error. Uncertain
network results require refreshing before retrying; no automatic retry is made.
Undo uses the same version-checked path. Task status is not changed locally until
the server confirms it, and access expiry never restores cleared private state.

Completion no longer performs the follow-up dashboard, importance-level, and
health requests, or rerenders chat/proposal editors. This reduces the normal
completion path from four HTTP requests to one. Backend task edits retain their
owner lock, version check, workspace revision bump, and audit event while using
six SQL statements instead of eight. These are request/query-count reductions,
not measured remote latency claims. Sample completion remains local.

Verification uses isolated SQLite plus a simulated browser controller with
deferred responses. It checks immediate feedback before confirmation, saved
versions, undo, network failure, version conflicts, unexpected responses, access
expiry, and preservation of chat. The user owns the running terminal; no server
was started or restarted for these checks. Reload the page, and restart the
backend from that terminal if it is not running with automatic reload.


### Direct task creation (October 30)

This replaces the earlier review-before-save product flow. The chat now creates
and updates actual tasks in one request, followed by one dashboard refresh.
The task editor remains the place for direct corrections; handoff classification
is still generated with the breakdown. Saving a task does not execute its work,
change its completion status, or start a machine session.

Restart your backend after this update if you are not using automatic reload,
then refresh the page. No database migration or new provider configuration is
needed. No server was started or restarted by this change.

Verification of direct saving: 131 automated tests pass. Coverage includes
immediate task persistence, classified steps, follow-up corrections, retry
idempotency, stale responses, ownership, transaction rollback, failure text
preservation, cleared user assessments, legacy compatibility, and the browser
submission/rendering controller with simulated interfaces. Two real Meta calls
using synthetic workshop data verified direct creation and a follow-up rename;
a manual child-task correction survived the rename and a fresh app instance.
The live check used disposable SQLite and did not start a server or change the
configured workspace. Visual browser QA remains for the user's running app.

### Keep the outcome visible above its next action

Priority cards now show the parent task as the primary heading, with a separately
labeled **Next action** underneath. Select the heading to edit the parent task;
the next-action checkbox still completes only that step. Tasks without steps
show their own title once. The sample day uses the same hierarchy.

This addresses the assessment case where the model had saved **Complete Duolingo
take-home assessment**, but its only child, **Share current brief and confirm
deadline**, was visually promoted over the actual outcome. Planning guidance now
keeps clarification questions in chat and requests substantive work stages at
the level supported by the known facts. Unknown briefs support a broad scaffold
(requirements review, required work, and checking the result); specific tools,
deliverables, or exact dates must not be invented. Existing clarification-only
plans should be improved by saved task/step IDs rather than duplicated.
