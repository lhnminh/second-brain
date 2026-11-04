# Visual Second Brain


**Current direction (November 4):** Browser/computer control is removed. Handoff
uses internet-enabled task chat. Input starts at one line and grows to six lines
before scrolling. Earlier browser execution notes below are historical. Document
attachments are available in General and task chats using the paperclip button.

**A new way to interact with AI agents. The future is visual.**

Working with an AI agent should feel as natural as seeing a plan take shape.
Your priorities, tasks, next steps, and the agent's activity belong in a shared
space you can understand at a glance and change directly.

Visual Second Brain is building that space: a daily dashboard where you and your
agent work together. Start with a mostly blank canvas, tell Muse what you need to do, and watch a
actual tasks take shape on the dashboard. Return to saved work when you need it. Less time reconstructing context. More room to
think and get things done.

## See it. Shape it. Move forward.

The vision goes beyond a conversation window. You shouldn't have to describe
every change in a message or scroll through a transcript to find out what is
happening. The interface itself should be how you steer the work.

- **See what matters.** Bring priorities, commitments, and next actions into view.
- **Shape the plan directly.** Edit a task, adjust its importance, or revise a
  suggested step where it appears.
- **Understand the agent's work.** See its planning activity, saved changes, and
  which tasks can be handed off to Muse.
- **Carry your context forward.** Return to a workspace that remembers your
  corrections and the work you've already done.
- **Talk when it helps.** The broader experience includes a corner companion
  for conversation and voice input, alongside direct dashboard interaction.

The goal is to free up time and mental space. You bring the intent; the agent
helps turn it into a plan you can see and steer.

## The first experience

You have homework due next Sunday. Tell Muse through chat and the task appears
on your dashboard, with useful steps when your context supports them. Answer a focused question if details are
missing, then change the saved task directly or through a follow-up message.
There is no separate proposal form or save-plan step. Mark work complete, return
later, and pick up where you left off.

The current prototype supports manual and conversation-based task creation and corrections,
task and subtask editing, five importance levels, saved context, real Muse planning,
and direct saving of validated task updates. `/dev` provides a read-only developer console for model runs, request inputs,
proposals, saved objects, and change history. Each browser has its own saved workspace, protected by a shared demo access token.
Microphone recording and Meta transcription feed the reviewed text conversation (see `frontend/README.md`).
Automatic onboarding and an animated companion remain incomplete. Individual sign-in
is on the roadmap after the hackathon. The standard app plans work. An opt-in local browser worker can execute delegated
website subtasks; see [browser handoff setup](BROWSER_HANDOFF.md).

## Try it locally

From the repository root:

```sh
cp -n .env.example .env
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run second-brain
```

Manual creation, editing, completion and reopening work without an API key.
Use **+ Add task** beside either focus count: both forms take a task name and
optional named subtasks. Entered steps save together with the task, without a
model call during saving. The dashboard then asks Muse to assess each new subtask
in the background; missing model access never prevents saving. Existing tasks have **+ Add subtask** in their expanded list and
bubble details. Description fields are removed from the dashboard. Apply all migrations first; migration
`c42b193d7e61` adds the saved focus-section choice without moving existing tasks.

Add your `META_API_KEY` to `.env` to enable Muse planning and internet-enabled chat. Keep credentials in
that ignored file. Open [localhost:8000](http://localhost:8000/) for the dashboard
or [/dev](http://localhost:8000/dev) for diagnostics and saved objects.
A successful demo connection lasts eight hours across both pages and reloads.
Sign out ends access while keeping this browser’s workspace. A separate workspace
cookie lasts one year, renewed on use; clearing cookies or switching browsers
starts a new workspace.

On Windows, copy `.env.example` to `.env` if it does not exist. Get a Meta
Model API key from your team's Meta developer account and put it after
`META_API_KEY=`. This project's variable name is `META_API_KEY`; Meta's general
quickstart uses `MODEL_API_KEY`, which this app does not read. The existing
`META_BASE_URL=https://api.meta.ai/v1` and `META_MODEL=muse-spark-1.3` defaults
match the configured adapter. Never use the website demo access token as a model
key. Do not commit `.env` or paste the key into chat.

Restart the backend after saving the key (`Ctrl+C`, then `uv run second-brain`
from the repository root). Open the live workspace at
[127.0.0.1:8000](http://127.0.0.1:8000/). The dashboard has one saved workspace;
sample mode has been removed. Use the same hostname/browser to keep your workspace. Try: “Create a task
to prepare for an interview on November 6, 2026, with three subtasks.” Check
the resulting cards, click the blue **Ask Muse** button, send a correction, and reload to check
saved tasks and history. Inspect failed runs in `/dev` without exposing secrets.
Enter sends; Shift+Enter adds a line. Model billing/access and credits must be active
in the Meta account. Each new subtask receives a suitability assessment: **Hand off**
is available for Muse-suitable work and disabled for work requiring you. Failed
assessments offer a retry. Handoff starts work in that task’s internet-enabled chat. Ask Muse opens the same
chat without sending. Browser/computer control has been removed; a suitability
assessment alone never starts work.

Hosted testing uses the server's key configured in Vercel. A local `.env` change
does not configure or deploy the hosted site. The app uses Muse chat with web search,
without a connection to your laptop or a separate browser.
The API explorer is at [/docs](http://localhost:8000/docs). After updating an
existing checkout, run the migration command above and restart the server.

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


## Browser control removed (November 4)

Browser execution is removed. Run `uv run second-brain`; handoffs use task chat
with web search. Historical execution rows/artifacts remain untouched.

## General chat, task chat and trash

Talk to Muse opens General chat. Ask Muse opens a larger persistent task chat;
all of a task's subtasks use that same chat. Hand off task is beside its deadline,
and subtask Hand off buttons delegate the selected work into that conversation.
Muse can use real web search and show source links. Browser/computer control is
removed. Research and drafting results are returned in the task conversation.

Concrete task requirements now become grounded subtasks without a separate request
for a breakdown; vague task names do not justify invented steps. Both composers
are larger. Voice transcription fills the composer without a success banner.
Trash removes a task and its descendants from the dashboard with Undo, preserving
saved chats and results. Run migrations after updating; `e490ac621fb8` adds the
reversible-removal field. No existing task/chat records are deleted by migration.

November 4 verification: all 224 automated tests pass. Isolated real-Muse browser
checks verified contextual creation of three grounded steps, official-source web
research, a whole-task handoff in the existing task chat, separate General history
and drafts, optional browser setup, deletion/Undo for both focus sections and a
subtask, and restored task chat after Undo/reload. Desktop, 390×844 and 1226×540
checks found no outer chat overflow, including the expanded voice note. The
configured migration preserved existing task/chat/context/audit/browser-run counts.


November 4 follow-up: focus headers no longer show counts, short-term cards and
both chat composers are more compact, and long-term lists grow to the neighboring
short-term height before scrolling (natural height on mobile). Handoff is limited
to short-term work. Whole tasks require all leaf steps to be suitable for Muse;
tasks with no steps use their own assessment. These rules are enforced for new
chat/browser handoffs. Ask Muse remains available for long-term planning. Replies
render Markdown and remove opaque native citation codes from old and new output,
while preserving verified source links.

Follow-up verification: 227 automated tests passed. Isolated desktop fixtures
verified matching panel heights once long-term overflow begins, natural expansion
without overflow, eligible and mixed handoff controls, and the pasted citation
example. At 390×844, task chat had no outer/horizontal overflow and long-term
entries had natural height without their own scrollbar. No live user tasks or
chat records were changed for these layout checks.


Chat-only verification (November 4): the retired browser routes return 404 and
are absent from OpenAPI. Source/entrypoint/config and optional Playwright/pyee
lock entries are removed. Historical database record counts are unchanged.
The remaining automated suite has 199 checks; all passed across the full run and
focused correction rerun. Desktop/mobile UI checks verified one-line empty input,
three-line growth, a six-line cap with internal scrolling, soft wrapping, shrinking,
and restored task drafts. Typing previews were never sent to Muse.


### Chat files and longer voice recordings

Use the paperclip in either chat view to attach PDF, TXT, Word `.docx`, PNG,
JPEG, WebP or GIF. Up to five files, 4 MB each. Remove a chip before sending or
retry an upload if it fails. Files sent with a message remain downloadable and
available for later questions in that chat. No guideline-specific format or
prompt is required. Word supplies text; export it as PDF when visual layout or
embedded images matter. Legacy `.doc` needs exporting first.

Voice capture allows three minutes. Stop & transcribe fills the editable draft;
it never sends the message automatically. Audio is uploaded in small parts and
is not saved by this app. The existing server Meta API key handles both features.

After pulling this version, run `uv sync` and
`uv run alembic -c backend/alembic.ini upgrade head`, then restart the server.
The attachment migration adds a table and preserves existing tasks/chats.
