# Conversation canvas and development workspace

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

1. Start with a full-width workspace canvas. Click the circular Muse launcher
   at the bottom right to expand chat. No task form is required.
2. Answer clarifying questions or review the task objects and steps Muse proposes.
   Proposals appear above saved plans on the wider canvas; the Muse panel links
   to pending reviews. They remain unsaved until explicitly approved.
3. Revise through chat or edit proposed titles, descriptions, and deadlines directly.
   You can remove unwanted tasks or steps. Follow-up messages carry unsaved edits.
4. Save the reviewed plan. Persisted task objects become cards on the canvas.
5. Edit saved tasks, choose among five importance levels, or mark work complete.
6. Return to saved tasks with a fresh chat on each page load or login. Demo login stays connected for
   eight hours across both pages and reloads; Sign out ends access while retaining this browser’s workspace.

Model proposals remain separate from saved work until accepted. Conversation
corrections can update existing task objects; steps append to existing plans.
The model can correct an existing step by ID. The UI renders fixed task components,
not generated HTML or arbitrary widgets. See `API_CONTRACT.md` for object shapes.

## Development tools

`/dev` is a read-only diagnostic console rather than a second task-editing UI:

- Snapshot counts, configured model, account, access mode, and service liveness.
- Filterable model runs with actual input, review drafts, proposals, errors,
  timestamps, related messages, and linked events.
- Searchable saved tasks, context, and messages, with field and JSON inspectors.
- Searchable change history and the full account snapshot.
- Manual refresh and optional ten-second refresh while the page is visible.

Proposals are reviewed on the workspace. The console labels pending changes,
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
proposal-review flow. No task changes are saved until you approve the proposal.

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
request, then bring the resulting review into view. Sending, editing, approval,
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
   appears in Muse without being sent. Send it manually, review the real proposal,
   save it, and reload to check persistence using the normal app flow.

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
