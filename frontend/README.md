# Conversation canvas and development workspace

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
5. Mark work complete and return later to the saved state. Each page load or
   login still starts a fresh chat; saved tasks and user context carry forward.

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

The workspace registers four tools through `document.modelContext.registerTool()`:

| Tool | Behavior |
| --- | --- |
| `get_dashboard` | Fetch saved tasks and pending proposal IDs using this browser's authenticated workspace. |
| `draft_muse_message` | Open Muse and stage text for the user to review and send. Preserve existing unsent text. |
| `open_task_editor` | Open a loaded task for the user to edit and save. |
| `show_pending_reviews` | Scroll to and focus pending proposal reviews. |

These tools support the existing journey: inspect saved homework, stage a planning
request, then inspect the saved tasks. show_pending_reviews supports only earlier unsaved plans. Sending, editing, approval,
and persistence still use the existing visible controls and backend contracts.
The tools do not invoke Muse or save changes themselves. UI actions refuse to
interrupt requests, voice capture, or an open editor. Saved-state reads go to the
server each time and return an error rather than cached data if access expires
or the request fails. Results exclude conversation history, owner IDs, and internal
importance scores; `user_importance_level` is the user's choice and can be unset.

For local setup:

1. Start the app using the commands above and open `http://localhost:8000/`.
2. In a compatible Chrome build, enable `chrome://flags/#enable-webmcp-testing`
   and relaunch, following [Chrome's WebMCP instructions](https://developer.chrome.com/docs/ai/webmcp).
3. Reopen the workspace and connect using the normal demo access form if prompted.
4. Check `typeof document.modelContext?.registerTool` in DevTools; expect
   `"function"`. Use a WebMCP-capable browser agent or the tool inspector linked
   in Chrome's instructions to discover the four tools.
5. Call `get_dashboard`, then `draft_muse_message` with
   `{"message":"Help me plan my homework due next Sunday."}`. Check that the text
   appears in Muse without being sent. Send it manually, inspect the saved tasks,
   correct one, and reload to check persistence using the normal app flow.

Registration requires a secure context (HTTPS or localhost) and the current
`document.modelContext` API. Browsers exposing only the older
`navigator.modelContext` API are not supported by this integration. Unsupported
browsers retain the normal UI. No polyfill, third-party script, new dependency,
remote MCP server, or cross-origin tool exposure is added. Tools unregister on
page exit and register again on back/forward restoration. This adds website-side
tools; it does not configure an agent client or enroll the deployed origin in
Chrome's origin trial.

Verification: automated Node tests execute the shipped tool code with simulated
browser and network interfaces. They cover discovery/registration, unsupported
browsers, input validation, authenticated read options, access/network errors,
cancellation, preservation of drafts and edits, and navigation cleanup. They do
not verify native WebMCP discovery in Chrome or a deployed browser-agent journey.

## Three-panel dashboard draft (October 30, 2026)

The workspace uses the available desktop width and shows:

- **Current priorities:** up to three next actions, one unfinished leaf step per
  eligible plan, ordered by the existing importance score. The plan name provides
  context. Expand for remaining steps, notes, and plan editing/completion controls.
- **Long-term focus:** eligible saved tasks without a deadline, using the same
  task model as the rest of the dashboard. Shows three initially, with further
  items behind a disclosure. Select a task to open its bubble details. A task can
  also appear among current priorities when its importance ranks highly.
- **Everything to do:** a responsive bubble map of every eligible top-level task/plan,
  including work beyond the three current priorities. Larger bubbles represent greater importance. Each bubble shows a short task
  name and importance label; selecting one opens its steps and editing controls
  beneath the map. Selecting it again or closing details collapses that view. This replaces the earlier completion-calendar draft.

Importance appears through bubble size, color, and the existing five labels.
Bubbles use existing user-selected levels or backend score ranges;
internal scores are never displayed. Unassessed tasks have an explicit label and
a neutral bubble. Ordering uses backend importance scores in live mode.

Completed plans and plans with all leaf steps complete leave both active views.
The **Completed work** disclosure retains access to these saved plans. This is a
visibility rule: it does not delete records or automatically complete parents.
Reopening a step makes an incomplete parent eligible again.

Completing a visible action checks it off and fades it upward, followed by the
next action sliding into place. Live motion waits for the write and refreshed
dashboard to confirm completion. Failed requests do not play success motion;
canceled animations still allow updated state to render. Reduced-motion
preferences skip animations. Sample steps use the same motion without saving.

Choose **Preview sample day**, or open `http://localhost:8000/?draft=1`, to see
populated fixtures, including living-room, garden, and photo projects. A visible
**Design draft · sample data** label marks this mode. Sample completions stay in
memory and reset on reload. **Back to my workspace** returns to live tasks.
Fixtures never enter API state, proposal review, or Muse context. Chat still uses
the real workspace and existing backend; sample mode does not simulate Muse.
No backend/API changes or frontend dependencies were added.

Verification: all 8 existing frontend, voice, chat lifecycle, and WebMCP checks
pass. Temporary Node harnesses with simulated DOM/animation interfaces checked
three default focus actions, nested step ordering/advancement, completed-plan
removal, preservation of parent status, isolated sample changes, the full backlog,
house-project steps, five-level/unassessed importance, escaped titles, animation
cancellation, reduced motion, and failure behavior. Visual review is left to the
user at their request. No live model calls were made for this draft.


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
its detail panel with height and fade motion. Repeated clicks can reverse a
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
