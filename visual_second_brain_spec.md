# Visual Second Brain — Product Spec

**Status:** MVP product scope defined; technical integration and implementation details open  
**Version:** 0.35
**Date:** November 4, 2026\
**Format:** Hosted web application  
**Working name:** Visual Second Brain

## 1. Product vision

**A daily starting point that frees up time and mental space.**

Visual Second Brain is a visual dashboard you open daily, especially at the start of your day. It brings together priorities, work that needs doing, and work already underway so you can understand where things stand and get on with your day.

**Confirmed interaction direction:** Start with a mostly blank canvas and a prominent
text conversation. The user describes what they need to do; Muse proposes structured
task objects and their plans, and the frontend renders them as editable cards. Validated task objects save directly and appear on the dashboard. The user
corrects saved tasks through direct editing or follow-up conversation. Saved
objects populate the canvas on return; no proposal editor or approval step is
required for new chat requests.
Muse creates task data, rather than generating arbitrary UI code or widget types.
The desktop workspace always uses the same canvas-left/chat-right layout, including
when no tasks exist. The empty canvas has a quiet placeholder rather than a separate
centered onboarding screen. `/dev` is a dedicated read-only diagnostic console for
runs, requests, proposals, saved objects, messages, and change events.

The experience combines three parts:

- **Daily dashboard:** See short-term and long-term priorities, current focus, and next actions.
- **Agent activity:** See subtask creation and importance-scoring activity. The broader vision adds steps and screenshots for screen-based execution.
- **Conversation:** Start and revise tasks through prominent text chat. Microphone recording and Meta transcription feed the reviewed text conversation; a corner pet remains planned.

Conversation builds the initial workspace. Once saved work exists, the canvas provides useful context at a glance without requiring the user to reconstruct their situation from message history.

**Agent platform:** Muse. Users can provide voice or text input, and the agent can reply in text chat and update the dashboard. Spoken agent replies are outside the MVP scope.

## 2. Users and onboarding

**Hackathon decision:** Use one anonymous workspace per browser profile and app origin; individual sign-in is on the roadmap. A persistent HttpOnly cookie identifies the workspace, and every record retains `user_id` for isolation. Tasks, context, diagnostic conversation history, and agent runs are separate between browsers, even when they use the same demo access token. Reloads and backend restarts preserve access while the cookie remains. Sign-out ends demo access but keeps the workspace cookie.

The workspace cookie lasts one year, renewed on use. Clearing cookies, private browsing, another browser, or a different app origin starts a separate workspace. Account recovery and cross-device linking require future sign-in. Existing shared-demo records remain untouched and are not automatically assigned to a browser.

**Chat lifecycle (November 3):** General and task-specific conversations persist
in the browser workspace's server-side records. Each root task has its own
conversation scope; subtasks share it. Task chats include their original creation/correction messages
when audit records link that run to the task. Reloading or signing in again does
not discard history. The last selected task is remembered locally per workspace;
unsent drafts remain in memory and are kept separate while switching chats.
The optional visit-scoped API mode remains available for older clients.

**Dashboard refinement (November 3):** Keep short-term focus left, long-term focus
right, and task bubbles below. The date is the main heading; the app name stays
in the top bar without a logo. Each overview task has one closed-by-default
disclosure containing every leaf subtask in saved order, including struck-through
completed steps; bubble details show their subtasks or description directly with
no nested dropdown. Show explicit task
counts and each task/subtask's own saved deadline. The long-term summary and
Muse header icon are removed. Nested text surfaces allow scroll chaining.
Progress counts only the displayed subtasks, never the parent. Selecting or
switching bubbles reveals details below without scrolling the page or moving
focus into the panel. Keyboard focus stays on the selected bubble. All short-term
index badges use the same neutral styling; the first item has no special status. Enter sends chat; Shift+Enter adds a line. Saving/planning still does not execute the underlying work.

**Task creation correction (November 3):** A request to create a task does not
request a breakdown. Muse must default to `subtasks=[]`, creating steps only when
the current message explicitly requests a breakdown/checklist/subtasks or supplies
the steps to save. Missing details belong in chat or a short description. Do not
automatically expand or repair saved steps during unrelated corrections. This
supersedes earlier automatic work-scaffold guidance. The provider instructions implement this default; isolated live checks now verify
creation with zero steps and an explicitly supplied two-step plan.

**Separate focus views (November 3):** A saved `time_horizon` selection pins a root
task to short-term or long-term focus. Unselected legacy/model-created tasks keep
the previous inference: dated tasks or tasks with saved leaf steps go on the left;
remaining undated tasks without steps go on the right. Short-term tasks sort by
earliest deadline, with undated plans last and importance breaking ties. Long-term descriptions open through a dedicated right-hand chevron; all entries share one scrollable list. No task appears
in both focus panels. The bubble map still contains all active root tasks.
Deadline badges range from red (overdue or due within one day), orange (two to
three days), yellow (four to seven days), to green (more than a week). The optional focus field is now implemented for manual creation and editing.

**Past tasks and chat entry (November 3):** A separate Past tasks section retains
completed roots and pending roots whose leaf steps are all completed. Rows show
a read-only name, completion label, and **Reopen task** only. Past tasks are grouped
under **Short-term** and **Long-term** headings using the same saved focus choice
and fallback inference as active tasks. There are no child controls, chat buttons or editors in this
section and no separate top navigation link. “All subtasks completed” does not
silently mark the parent complete. Reopening preserves completed children; a
fully checked plan returns as `in_progress` so it stays active until completed
again. Other reopened tasks return as `pending`. Saved chats remain attached and
become accessible from the active task again. “Ask Muse” opens the existing persistent chat
for the exact saved task or subtask; it creates no new conversation, sends no
message, and starts no execution. Complete
task stays last at the right of each action group. Live API access is available locally; computer/worker integration remains deferred.

**Header refinement (November 3):** The sample workspace and its switch are removed.
The dashboard always shows the saved browser workspace. Workspace and the voice-transcription disclosure use centered chevrons that
turn on expansion, replacing the misaligned text glyphs. The header shows the
app name without the former “Your day, at a glance.” tagline.

**Manual tasks and inline content (November 3):** Both focus headers have **+ Add
task** directly before the task count. Short-term creation takes a task name and
numbered subtask rows, with **Add subtask** and removal controls; at least one step
must be entered. It has no description field. Long-term creation takes a name
and optional description, without subtask rows. Both forms offer optional deadline
and importance fields and preserve the selected focus section. The authenticated
API saves the short-term root, entered children and audit events in one transaction.
It makes no Muse call and invents no steps. Existing task notes remain preserved.

Names, descriptions, subtask content and deadlines remain editable in place;
button labels, section headings and derived counts are interface text. Names save
on Enter/blur, descriptions on blur or Ctrl/Cmd+Enter; Escape cancels the active
edit. A long-term name only edits that name. A separate chevron button on the right
opens/closes its description, with keyboard support and an expanded-state label.
Migration `c42b193d7e61` adds nullable `time_horizon`; this refinement needs no
additional migration. Tests use fixtures; isolated live Muse checks verify task creation, focus changes,
minimal descriptions and automatic task-chat selection.

**Chat and editing correction (November 3):** Only root tasks have separate saved
chats. A subtask's Ask Muse action opens its root's chat; older subtask-scoped
messages remain saved and visible there. Successful single-task creation or an
unambiguous task discussion automatically selects that task's chat. The model
returns a validated existing `chat_task_id` for task-specific answers and a
`time_horizon` when moving work between focus sections; the backend saves the
choice before returning success. Omitted/null focus on older proposals preserves
an existing choice. Multiple ambiguous tasks do not force a chat switch.

Sending immediately clears the composer while the message appears in history;
failed sends restore the text, preserving the request ID for uncertain outcomes.
A confirmed successful send stays cleared even if a later UI refresh fails. The
chat header, selector, composer and voice disclosure remain in a bounded flex
panel; messages use its remaining scrollable space. Subtask descriptions are
collapsed by default and open through a side button before Ask Muse. New model
descriptions default to empty and contain only supplied facts when needed.
Long-term entries show their deadline first, actions next, then Go to task chat.
Edit task contains only short-/long-term focus, five importance choices and a
You/Muse handler. Names, descriptions, dates and completion stay on the dashboard.
Existing classification context remains stored. No migration is required.

**Name-only tasks correction (November 3):** This supersedes earlier description
fields, description buttons and separate long-term creation forms. The dashboard
shows task names and consistent editable subtask names, with no task/subtask
description text blocks. Both focus sections use the same optional named-subtask
creation controls, and existing tasks expose **+ Add subtask** in the expanded
list and bubble details. The long-term chevron opens its subtasks and actions.
Bubble steps remain directly expanded. Names use the same renderer and typography.

A new task can have zero steps. Manually added steps save without model calls in the save transaction;
Muse still creates steps only on explicit request. Context belongs in saved task
chat. Existing description data remains stored and is preserved during unrelated
edits. Older tasks with inferred focus are pinned to their current section before
adding a child, so an undated long-term task does not jump to short-term focus.
No schema migration or data deletion is required.

**Task actions and subtask suitability (November 3):** This supersedes earlier
sample-mode, task-chat button, handler-editor and keyboard directions. Blue **Ask
Muse**, **Edit task**, and **Complete task** share one action row. Short-term rows
remain visible when subtasks are folded; long-term rows appear inside the expanded
panel. The task editor contains only focus and importance. Enter sends chat;
Shift+Enter inserts a newline.

Manually entered subtasks save first, then Muse assesses their suitability in the
background. Chat-created subtasks already carry validated assessments. Each step
has a right-aligned **Hand off** control; human work is disabled, unassessed work
can request an assessment, and failures offer a retry without losing saved steps.
The dedicated authenticated assessment endpoint validates exact IDs, ownership,
versions and structured output, records an idempotent diagnostic run, and changes
only suitability metadata. It creates no chat messages and starts no execution.
User-assigned classifications cannot be overwritten. No computer/worker is yet
connected: enabled Handoff opens an explicit setup notice, leaving work unchanged.
No database migration or new dependency is required.

**Internet task chats and contextual plans (November 4):** This supersedes the
previous explicit-breakdown-only policy and chat/browser entry directions. A bare
title or deadline can remain one task, but concrete user context and requirements
should proactively produce a small useful set of grounded named subtasks. Do not
invent requirements, generic scaffolds or steps during unrelated corrections;
respect explicit no-subtask instructions and preserve accepted work.

Talk to Muse always opens persistent **General chat**, without a task selector.
**Ask Muse** opens the root task's persistent conversation in a larger dialog;
subtasks share that conversation. Whole-task **Hand off task** sits to the right
of the deadline; subtask handoff enters the same root chat with that subtask as
its delegated context. Handoff sends a work request to the internet-enabled Muse
assistant. Ask Muse opens without sending. Current clients keep new exchanges in
the chosen General/task scope instead of automatically changing chats. Older saved
histories remain intact. Drafts remain distinct while switching surfaces.

Internet chat uses Meta's Responses API and built-in web search, strict structured
output, validated task updates, actual search metadata and source links. It can
research, analyze and write usable replies; it does not claim external writes,
browser clicks, downloads or physical execution. **Use browser** is a separate
optional task-chat button, opening explicit browser setup. Only **Start browser**
launches computer control. The optional worker accepts whole tasks with their
saved subtask context, and interrupts on task/ancestor/descendant edits or removals.
Saved browser results appear in the root task conversation.

Both chat surfaces have larger composers; the task dialog uses most of the screen.
Only the message history needs scrolling. Successful transcription populates the
composer without a success notification; genuine failures remain visible.

**Reversible removal (November 4):** Trash sits below short-term numbering, before
a subtask checkbox, and beside the long-term expand control. Removing a task hides
its descendants and bubble together, with Undo. Migration `e490ac621fb8` adds
nullable `deleted_at`; task rows, relationships, chats, browser artifacts and audit
records are retained. Removed task chats remain scoped to their task and are
hidden from General. Undo restores the same IDs and history, preserving children
that had been deleted independently. Version checks, ownership, request retries
and revision changes protect against stale writes. The last 20 Undo items are kept
per browser workspace in session storage; there is no permanent purge interface.

This slice addresses reconstructing work and switching between planning and action:
a user gives context, sees grounded steps, delegates research in the same task
chat, corrects saved work, and returns to preserved state. It demonstrates useful
Meta model/tool execution and reliability. Verify source-backed replies, grounded
step creation, scope isolation, Undo, optional browser entry and state on return.

**Dashboard density and handoff correction (November 4):** Short/long focus headers
omit task-count badges. Short-term cards use tighter spacing. On desktop the
long-term list grows to the short-term panel height before scrolling; on mobile
it grows naturally. Both chat composers are compact, and the internet availability
subtitle is removed. Replies render readable Markdown and hide opaque provider
citation codes in old and new messages while preserving verified source links.
Handoff is only available for short-term work; every leaf subtask must be assessed
for Muse before the whole task is enabled. A task without steps uses its own
assessment. Long-term tasks and their steps keep Ask Muse without handoff/browser
entry. The backend enforces the same eligibility for new delegated chat/browser
requests; existing histories and browser results remain accessible.

**Interaction repair (November 4):** Deletion notices dismiss after eight seconds
or with Close; Workspace retains Undo last deletion for the saved recovery stack.
Subtask completion has no exit/reentry animation and renders the confirmed result
once, preserving keyboard focus on the same checkbox when possible. Bubble details
use a full-width title and separate deadline/action row, without a nested scroll
limit or automatic page movement. Both chat surfaces put input and send/voice
controls on one compact row, leaving more room for history. Past tasks keeps only
the separate short-term and long-term counters.

**Stable completion and bubble navigation (November 4):** Checkbox saves update
only the affected row, version, progress and handoff control; unrelated controls
and the bubble physics remain mounted. A finished plan alone moves into history.
Bubble selection replaces only its details and scrolls their bottom to the viewport
bottom with a small margin; reduced-motion uses instant scrolling. This supersedes
the prior stay-in-place behavior. Chat textareas default to four lines while still
allowing smaller/larger manual sizing. Subtask checkboxes align with the first
name line. The Workspace label/chevron share a centered row. Page-top informational
save notices are removed; failures remain visible.

### Voice-first onboarding

The intended onboarding experience is open-ended voice input with text chat replies from Muse. The user can talk freely about who they are, what they are involved in, and their general focus. The agent should accommodate an unstructured explanation rather than require a detailed form or a polished plan.

A proposed flow:

1. Invite the user to talk about themselves and what is currently on their mind.
2. Let them explain in their own words; Muse can ask brief follow-up questions in text chat when needed.
3. Extract an initial understanding of their context, broad focus, and any priorities or goals they mention.
4. Present that understanding for correction or confirmation.
5. Use the confirmed context to populate their first dashboard.

Specific tasks, deadlines, and priorities should only be populated when supported by what the user says or subsequently confirms. Broad aspirations can remain broad; onboarding does not need to produce a complete task list.

The Muse integration details for voice input, transcription, and audio retention remain to be defined. Text input is also available; spoken replies are not required. Microphone use should have clear listening controls. The context carried forward from onboarding should be visible and editable by the user.

## 3. Daily dashboard

| Content | Purpose |
|---|---|
| Priorities | Understand what matters most |
| Short-term view | See what needs attention soon |
| Long-term view | Keep larger goals and direction visible |
| Work to do | Understand what needs to be done |
| Currently running | See agent tasks underway and their status |
| Current focus and next actions | Decide where to put attention and how to move forward |

These are content needs, not a prescribed set of panels. A new workspace starts mostly empty, without task forms, statistics, or prefilled panels; task cards appear as the user accepts conversation proposals. The layout should make the overall situation easy to scan, with details available when needed.

Proposed interactions include adjusting priorities, editing work, choosing a focus, and accepting or revising suggested next actions. Connecting near-term work to long-term goals could help explain why an action matters.

Useful context should persist between visits. User corrections and completed work should inform subsequent suggestions.

### Importance: simple user choice, granular agent scoring

**Decision:** Users choose one of five importance levels. The agent maintains an internal integer `importance_score` from 0–100 for finer ranking.

- The user interface shows five choices, with no slider or numeric entry.
- Each level maps to a score range. A user-selected level constrains the agent's score to that range.
- The agent can refine the score within the selected range to distinguish similarly important items without overriding the user's choice.
- The dashboard displays the importance level rather than the internal score.
- Importance stays separate from deadline and urgency. An approaching deadline may raise priority without changing importance.

This keeps fine-grained scoring with the agent and reduces the user's decision burden. Confirmed labels and score ranges:

| Label | Internal score range |
|---|---|
| Very low | 0–19 |
| Low | 20–39 |
| Medium | 40–59 |
| High | 60–79 |
| Very high | 80–100 |

**Decision (October 30):** Generated task breakdowns, importance scores, and
handoff classifications are validated and saved directly when the user describes
concrete work. The user corrects the actual task afterward. Server-side
validation, ownership, stale-update protection, and audit history remain required.
Saving tasks does not authorize execution of their underlying work.

## 4. Agent activity

For the MVP, agent work consists of creating subtasks and assigning importance scores. Activity should show that work's status and resulting changes. Completing a planning run does not mean the user's task is complete.

### Broader vision: screen-based activity

The following screen and screenshot experience applies when the agent later performs work with a visual surface; it is not required for subtask creation or scoring.

The user can open a running agent task to see what is happening and how it is progressing.

The task view should include:

- The task and its current status.
- The current step and a history of steps taken.
- Screenshots associated with relevant steps.
- Results and any point where user input is needed.

A screen view may also show the task as it runs. Whether this uses live viewing, periodic screenshots, or step-linked captures remains open.

Steps describe observable actions and results. Tasks without a screen should still expose useful progress. Status should reflect actual execution and indicate when information is stale or unavailable.

## 5. Corner pet and conversation

A small pet sits in a corner of the application. Activating it opens text chat with optional voice input to Muse. Voice input is available throughout daily use, including after onboarding. The agent replies in text chat; it does not speak back in the MVP.

The user can speak naturally or type to ask questions, discuss priorities, update their context, request work, or steer an ongoing task. Conversation should share the dashboard's context, including relevant user edits and task state.

The dashboard remains useful with conversation closed. The pet's appearance, animation, and any activity indicators are design decisions. Voice input should have explicit listening controls and a visible listening state.

## 6. Role of the agent

The MVP agent creates tasks and their plans from natural language, asks for missing information, and proposes corrections to existing tasks. Its planning capabilities include:

1. **Create subtasks:** Break a task into concrete steps that help complete it.
2. **Score importance:** Assign or refine internal 0–100 importance scores using available context and respecting any user-selected importance level.

The user can edit the breakdown and choose among five importance levels. Suggestions should reflect the latest user changes. Deadlines must come from user-provided or confirmed context rather than being invented during decomposition.

External task execution and broader autonomous behavior are outside this initial capability set.

### Core task model

Tasks and subtasks use the same structure. A subtask references its parent through `parent_task_id`; a top-level task has no parent.

| Field | Purpose |
|---|---|
| `id` | Identify the task |
| `user_id` | Scope the task to its owner |
| `parent_task_id` | Link a subtask to its parent; empty for a top-level task |
| `title` | Describe the work to complete |
| `description` | Optional supporting context |
| `deadline` | Optional deadline; empty when unknown or not set |
| `importance_score` | Internal integer from 0–100; empty until assessed |
| `user_importance_level` | Optional user-selected level, constraining the agent's score |
| `status` | Track pending, in-progress, or completed work |
| `created_at`, `updated_at` | Track creation and changes |

This is the core work model, supported by per-user onboarding context, conversation history, and agent activity records. Separate goal and project entities are not required for the initial MVP.

Parent and child tasks must belong to the same user, and parent relationships must not form cycles. Subtask ordering, parent completion behavior, and any propagation of deadlines or importance still need definition.

### Supporting user context

Persist context as structured, user-scoped records that can be queried and updated individually. Markdown summaries may help with reading or agent context, but should not be the sole source of truth.

The working context categories are:

| Category | Examples |
|---|---|
| About the user | Roles, responsibilities, interests, preferences |
| Long-term direction | Aspirations and what matters to the user |
| Current situation | General focus, commitments, constraints |
| Work state | Tasks, subtasks, completion, and agent activity |
| Assistance preferences | How the user wants help and relevant permissions |

These categories do not require separate tables or additional MVP goal and project entities. Concrete work belongs in task records; other context supports interpretation and scoring.

Context should retain its source, update time, and whether it was user-stated, user-confirmed, or agent-inferred. User corrections take precedence over conflicting inferences. Permissions require explicit authorization and must not be inferred from personal context.

A relational database with flexible JSON fields is the proposed storage approach; Postgres was suggested, but the database choice and final supporting schema remain open.

## 7. Experience principles

1. **Save time and mental space.** Each feature should reduce effort or the need to remember and reconstruct context.
2. **Make the situation visible.** Use visual hierarchy and clear status to support a quick daily overview.
3. **Support direct interaction.** Let the user correct and update information where it appears.
4. **Keep conversation accessible.** Text and voice are available through the pet when useful.
5. **Make agent work inspectable.** Show progress, steps, evidence, and outcomes.
6. **Carry context forward.** Preserve useful state and intentional user changes between visits.

## 8. MVP flow

Use one concrete daily scenario to demonstrate the complete experience:

1. Open a mostly blank workspace and describe homework due next Sunday through text chat.
2. See actual saved tasks and useful classified steps appear on the dashboard.
3. Answer any focused clarification questions and correct the saved tasks directly
   or through follow-up messages. Unsupported details remain unset.
4. Choose among five importance levels and adjust handoff classifications through
   direct task editing; no separate save-plan step is needed.
5. Continue the conversation to plan additional work or propose corrections. Inspect saved objects and activity at `/dev`.
6. Edit the breakdown, adjust an importance level, or mark work complete.
7. Return to the dashboard and see the updated state persist for that user.

The current end-to-end slice proves conversation-based task creation, decomposition, importance scoring, review, direct corrections, and persistence. Microphone recording and Meta transcription are available for the conversation; automatic voice onboarding and pet interaction remain planned MVP work. Screen streaming, screenshot capture, external integrations, and execution of the underlying work are deferred.

### Success criteria

- A new user can establish useful context by speaking naturally and correct the agent's interpretation.
- The user can quickly understand priorities, pending work, and agent activity.
- The experience reduces the effort of starting the day and keeping track of work.
- Direct edits inform subsequent agent interactions.
- Agent progress is understandable and reflects real execution.
- Useful context persists, giving the user a reason to return the next day.

## 9. Engineering requirements

- Enforce browser-workspace ownership on every data and task operation; retain the demo access gate for hosted use. Individual authentication is roadmap work.
- Use shared, persistent state within each user account for onboarding context, the dashboard, conversation, and agent tasks.
- Validate agent-generated updates before applying them.
- Preserve user corrections and handle conflicting or stale updates.
- Record meaningful changes and task events for inspection and recovery.
- Associate planning activity and resulting changes with the relevant tasks.
- When screen-based execution is added, associate screenshots with the relevant run and step.
- Authorize data access and agent actions; keep credentials server-side.

Decided stack: Vercel-hosted frontend, Python backend on Vercel serverless (owned in `backend/`), Neon (Postgres-compatible) database. The repository's Python scaffold migrates into the backend setup. Muse is the selected agent platform. Its integration contract and any hackathon requirements still need verification before those implementation choices are finalized.

### Implementation sequence

1. Verify Muse's integration contract for text and voice input, chat replies, structured task updates, and activity status. This is the first technical dependency to resolve.
2. Finalize the initial schema and implement browser-workspace isolation and persistence. Individual sign-in follows after the hackathon.
3. Connect onboarding context, subtask creation, and importance scoring through Muse.
4. Build the dashboard and five-level importance control.
5. Add the corner pet with text chat and voice input, without spoken replies.
6. Validate the complete flow, including saved state, user corrections, and isolation between users.

## 10. Open decisions

| Decision | What needs definition |
|---|---|
| First daily scenario | Confirmed: plan homework due next Sunday, review the proposed breakdown, correct it, and return to saved state. Ask for assignment details when needed rather than inventing requirements. |
| Context sources | Voice onboarding supplies initial context; what additional input or connected tools should keep it current? |
| Storage and context schema | Neon (Postgres-compatible) decided. Supporting record structures for the task model and user context still need definition. |
| Muse input and chat | How are voice input, transcription, and text chat integrated with Muse? What audio or transcripts are retained? |
| Importance levels | Confirmed: Very low 0–19, Low 20–39, Medium 40–59, High 60–79, Very high 80–100. |
| Priority and time horizons | Current view rule: dated tasks or saved plans on the left, remaining undated tasks without steps on the right; earliest deadline first. An optional saved time_horizon overrides this inference for manual task creation/editing. |
| Dashboard layout | Confirmed starting point: a mostly blank canvas with prominent chat; render structured tasks and plans as editable cards. Detailed visual design remains iterative. |
| Planning updates | Confirmed: validated chat updates save directly; users correct actual tasks afterward. Legacy proposals remain recoverable. |
| Task relationships | How are subtasks ordered, when is a parent complete, and do deadline or importance values propagate? |
| Running work | Should the dashboard include user work and other processes alongside agent tasks? |
| Future screen visibility | When screen-based execution is added: live view, periodic screenshots, step-linked captures, or a combination? |
| Pet and voice input | How does chat open, how is microphone input controlled, and does the pet indicate activity? |

**Implementation progress:** The initial text backend slice is implemented in `backend/`, with contracts in `API_CONTRACT.md`. A quick dashboard in `frontend/` is served at `/`. Browser checks with real Muse Spark and an isolated local database verified task/context creation, proposed subtasks, a user revision before approval, importance edits, completion, saved-state reload, and draft preservation after a connection failure. Neon persistence and deployment are not yet verified. Microphone recording and Meta transcription are implemented; automatic onboarding context extraction, streaming transcription, and real sign-in remain incomplete.


**Conversation canvas implementation:** `/` now starts with chat and renders saved task
objects as cards. Muse can propose new tasks with steps, answer clarification questions,
or propose edits to owned tasks. Proposals are validated and reviewed before atomic
application. Follow-up requests carry unsaved proposal edits. `/dev` provides a read-only diagnostic console for model requests, proposals,
saved objects, messages, and change history. A migration makes run task links
optional; existing task-planning endpoints remain supported. Subtasks append to existing
plans; edit existing steps by ID rather than replacing a plan. This is not arbitrary UI
generation, external task execution, or automatic onboarding extraction.


**Navigation and diagnostics refinement (October 27):** Empty and populated
workspaces share the same layout. Demo login establishes an eight-hour signed
HttpOnly session shared across `/` and `/dev`, including reloads, with sign-out.
This does not replace the planned real per-user authentication. The diagnostic
console distinguishes pending proposals from saved objects, reports actual run
states and linked events, and labels snapshot-fetch timing separately from run
lifecycle timestamps. It does not claim provider latency or model readiness.


**Voice input (October 27):** The composer records up to one minute through the
microphone, then **Stop & transcribe** forwards a validated WAV through the
backend to Meta Voice Transcribe (`muse-voice-transcribe-1.0`). Browser speech
recognition was replaced after its speech service failed in Dia. The transcript
is editable before Send and uses the existing conversation/review/save flow.
Audio is held in memory only, with no app-side disk or database retention.
Failures preserve typed text and allow explicit transcription retry; Cancel and
navigation discard audio. The transfer to Meta is disclosed before recording.
Sent transcripts persist as ordinary conversation messages; unsent drafts do not
survive reload. Automatic onboarding extraction and spoken replies remain open.
Automated checks use simulated capture/provider interfaces. A synthetic speech
sample was transcribed successfully through the real Meta adapter, and the user
confirmed the revised flow works in Dia on localhost. Hosted voice deployment
remains unverified.


**Browser workspaces (October 27):** Anonymous workspace ownership replaces the
shared demo owner. A persistent browser cookie selects isolated saved state;
the eight-hour demo access session is separately bound to that workspace.
No schema migration or automatic transfer of legacy shared data is performed.
Individual sign-in, account recovery, and cross-device linking remain roadmap work.

## Task assistance direction (October 30)

**Confirmed direction:** The dashboard makes pending work, available agent help,
and work needing human attention visible. Break tasks around clear outcomes,
useful handoffs, decisions, and independently reviewable results. The agent can
help the user get started and take delegated work on a connected computer.

**User correction:** Task interaction should offer a single **Hand off to Muse**
button. The intended flow hands the selected task to Muse working on a dedicated
machine. A separate text-drafting mode, artifact editor, and draft-save workflow
are not the desired task experience and have been removed.

Chat remains available for planning and clarification. In the future execution
flow, Muse may use chat to ask for missing information before proceeding. The
runtime and machine connection for that flow remain to be implemented.

**Current implementation:** Tasks and subtasks are classified during planning as
work Muse or the user can handle, including a reason, requirements, and a
concrete completion result. Classifications save with their tasks; the task editor supports corrections.
Only unfinished work classified for Muse shows **Hand off to Muse**; human work
shows **For you**, and old unclassified tasks show **Not assessed**. The sample
day contains explicit fixture classifications. No computer is connected. Clicking displays a clear
“No computer connected” setup message and leaves the task and chat unchanged.
It makes no model/API call, queues no work, and creates no execution run.

**Data preservation:** The draft-storage migration was already applied to the
configured database. Its table and historical draft records are retained; no
schema downgrade or data deletion is performed. The text-drafting generation
and save endpoints have been removed. Legacy records remain diagnostic history.

**Execution demo direction:** A spare computer should be operable by Muse and
the user, with visible progress, pause, human takeover, and resume. macOS or
Windows remains a setup choice. The local worker, machine connection, execution,
and screen viewer are not yet implemented. Only actual accepted worker activity
may change a task's execution status.


**Classification contract:** `handoff` is structured task data containing
`handler` (`muse` or `user`), `reason`, `requirements`, and `done_when`.
The model produces it in the same response as the task breakdown. Classification
is validated and saved with the task and remains independent of runtime readiness and
permission. User corrections are version-checked, audited, and preserved in
subsequent model interactions. Existing tasks and old pending proposals remain
unassessed unless reviewed updates or direct user edits classify them.
Migration `ae73dc160b52` adds nullable task fields without reclassifying data.


## Direct task interaction decision (October 30)

When the user defines concrete work, Muse puts it on the dashboard as an actual
saved task, with useful subtasks and handoff classifications. The user adjusts
those objects afterward. This supersedes earlier review-before-save references
in the implementation history. Broad personal context alone should not create
invented work; a concrete commitment can appear even when some details are still
unknown. Chat can gather those details as the saved task develops.

The frontend sends `apply_immediately: true`. Validated updates are saved
atomically before the reply returns, with idempotent retries, ownership checks,
revision checks, and audit records. Corrections made during a model call prevent
its stale updates from being applied. The API's existing review mode remains
for compatibility, and earlier unsaved plans have compact recovery controls.
No draft editor is shown for new work. There is no new migration or automatic
machine execution, and task completion remains a separate user action.

**Finished-history correction (October 30):** Completed tasks must not block new
commitments with similar titles. Muse receives active work and finished history
separately. Plans with all leaf steps complete are historical for planning even
if their stored parent status is still pending; this does not automatically
mark parents complete. A new Duolingo assessment is a fresh task even when an
older assessment is finished. Old requirements and deadlines must not be copied
into the new commitment. Recent chat/proposal text cannot override current work
state. The old record remains preserved and explicit corrections are supported.

**Outcome versus clarification (October 30):** The parent task must express the
user's intended outcome and be prominent in the priority card. The next step is
labeled separately so an information request cannot visually replace the main
task. Ask for missing inputs through chat. A take-home assessment with no brief
can have a broad requirements/work/check scaffold, while assignment-specific
requirements and exact dates remain unknown. Existing clarification-only plans
should be refined using their saved IDs rather than duplicated.

**Task naming and controls (October 31):** Task and subtask names are
inline input fields. Enter or leaving the field saves; Escape cancels the edit. A rename
preserves the task ID, saves across visits, and supplies the current title to
subsequent Muse requests. Task cards omit the “For Muse” badge and “Why?”
disclosure; the handoff button remains available for eligible unfinished work.
Classification details remain editable under Handoff settings. Machine execution
remains unimplemented.


**WebMCP task actions (October 31):** Browser agents can read saved dashboard
state, create tasks/subtasks, update task fields with version checks, send Muse
messages with request UUIDs, and apply/dismiss legacy conversation plans through
registered tools. These actions reuse the existing authenticated backend and
refresh the visible dashboard; browser clicks are optional for the task journey.
Reads include handoff assessments and explicit machine-execution unavailability.
Unsaved user edits are preserved. Ambiguous write responses require verification
rather than a success claim or blind creation retry. Automated checks exercise
the shipped tools against FastAPI/SQLite with simulated browser registration and
Muse responses; native browser discovery and hosted agent operation are unverified.


## Dedicated local-browser execution (November 3)

The user chose a dedicated browser on their laptop for the first execution slice.
This supersedes earlier blanket statements that all execution is deferred. The
concrete journey is a saved research subtask: Hand off, review the start URL and
optional instructions, start a separate browser, inspect progress, pause/take over
or stop, and return to saved results. It demonstrates actual Muse vision/tool
reasoning and an observable browser outcome. Automatic task completion remains
outside this slice: the user reviews the result and completes the subtask.

The opt-in local command runs one FastAPI process with one background browser
worker. Windows uses a fresh Microsoft Edge instance; other platforms use the
installed Playwright Chromium. Neither attaches to the user's usual browser
profile. The existing Meta key/model are reused through `/responses`, screenshots
and strict validated function tools (`browser_action`, `open_url`, `pause_for_user`).
The native computer tool rejected a synthetic screenshot for this account, so the
implementation deliberately uses the verified function-tool path, with no silent
provider fallback. No MCP server or cloud/GPU credits are needed.

Browser runs persist separately from planning/chat, with workspace ownership,
request idempotency, snapshots of the delegated goal, action summaries, screenshots
and download metadata. Files remain local under ignored `.browser-workspace`.
Start/control/artifact routes require the loopback app, normal workspace identity
and same-origin checks; hosted worker execution is disabled. Task/ancestor edits
interrupt the worker before further actions. Pause/Stop take effect at an action
boundary, discarding an in-flight model response. Resume observes a fresh screen.
A process restart marks active runs interrupted instead of replaying stale actions.

Limits: one run at a time, 20 model turns, a ten-minute active-run deadline checked
between turns, 20 retained downloads of at most 50 MB each. Paused time currently
counts toward that deadline; a paused browser stays open until Resume/Stop or
process shutdown. Public HTTP/HTTPS only; local/private destinations, host files,
clipboard shortcuts, service workers and WebSockets are blocked. This browser
profile is not a full VM/security sandbox. Pop-ups, uploads, website dialogs, login
and CAPTCHAs may require manual work or end a run. The model is instructed to
request human input for sensitive actions; this is not a production guarantee.
The UI shows results for review, never proof that an arbitrary goal was completed.

Migration `d785c418a901` adds `browser_runs` only; no existing records are deleted.
See BROWSER_HANDOFF.md for reproducible setup, demo and verification evidence.
