# Dedicated browser handoff

Hand off now uses an internet-enabled task chat by default. The local app also
offers an optional separate browser through Ask Muse → Use browser. In browser
mode, the model receives task context and browser-page screenshots, then requests validated mouse, keyboard or navigation actions.
Your normal browser profile, tabs and desktop are not attached.

This is a first local implementation. The hosted site cannot connect to your
laptop yet. No MCP connection, GPU or cloud account is required. Model requests
use your existing server-side `META_API_KEY` and incur normal Meta usage.

## Start it

From the repository root, stop the old local server and run:

```sh
uv sync --extra browser
uv run alembic -c backend/alembic.ini upgrade head
uv run --extra browser second-brain-browser
```

On Windows, the worker uses installed Microsoft Edge in a fresh temporary
session. It does not open or read your normal Edge profile. The downloaded
Chromium build failed to launch visibly on the development laptop, while Edge
was verified. On other platforms, install Chromium before starting:

```sh
uv run --extra browser playwright install chromium
```

Keep the existing `META_API_KEY` in the ignored root `.env`. No new key is needed.
The CLI explicitly enables the worker, binds to `127.0.0.1:8000` and runs one
process. Do not run multiple workers/processes against the same database.
The standard `second-brain` command leaves execution disabled unless the optional
`BROWSER_WORKER_ENABLED` setting is explicitly enabled.

Open [127.0.0.1:8000](http://127.0.0.1:8000/) in your usual browser. Continue using
that exact hostname/browser to keep the same workspace cookie. A different
origin or browser has a separate workspace; this command does not import hosted
tasks or another browser's data.

## First reproducible test

1. In Muse chat, ask: “Create a short-term task called Browser test with one
   subtask: open the IANA page linked from Example Domain and report its heading.”
2. Click that task’s **Ask Muse**, then **Use browser**. Whole-task browser runs
   include the saved subtasks; subtask handoffs share the same root conversation.
3. Set **Start website** to `https://example.com/`.
4. Click **Start browser**. A separate visible browser opens. The dashboard panel
   shows actual saved status, the latest page screenshot and action summaries.
5. Wait for **Run ended — review the result**. Check the screenshot and Muse's
   reported heading. The subtask stays unchecked until you complete it yourself.
6. Reload the dashboard and reopen **Ask Muse → Use browser**. Use **Saved runs** to inspect
   earlier runs, including failures. **Open full-size screenshot** shows the
   captured page at its original size. Download links retrieve saved attachments.

Ask Muse opens a conversation without sending; Hand off sends a task/subtask
request to internet-enabled Muse. Use browser opens setup, and only Start browser
launches computer control. Assessing suitability never starts work by itself.
An assessment means the work could suit an agent; it does not guarantee the
website, login, permissions or information needed for this particular run.

## Pause, take over and stop

- **Pause** requests a pause before further browser actions. Wait until the
  dashboard says **Paused — you can take over** before using the separate browser.
- **Resume** captures the current screen and has Muse reconsider it. Old actions
  from before the pause are discarded.
- **Stop** ends the run and closes its dedicated browser. A model request or
  browser action already in progress may need to return first; no later action
  is executed. Model requests time out after 45 seconds.
- Closing the dashboard panel alone does **not** stop execution. Reopen the
  task chat’s Use browser option or its saved browser-run card to see it again.
- Muse can pause for missing information or human work. Perform any appropriate
  supported step yourself, then Resume. Uploads, some pop-ups and dialogs are
  unavailable in this first version and may require stopping the run.

Editing/removing the task, any parent or a descendant, or adding new delegated
steps interrupts the run before further actions,
preserving the correction. Restarting the app marks abandoned active runs
**Interrupted** instead of replaying old clicks. A run ending does not certify
that an arbitrary goal succeeded and never automatically completes a task.

## What is stored and what is supported

Migration `d785c418a901` adds `browser_runs`; existing tasks, messages and planning
runs are retained. Browser runs are scoped to the same browser-workspace owner as
the task. Screenshots, summaries and downloads survive dashboard reloads and app
restarts. Files stay locally under ignored `.browser-workspace/<run UUID>/`.
Downloads use opaque storage filenames with sanitized names on the download links.
These artifacts are not synced to the hosted site and have no automatic cleanup.

One browser run can be active at a time. Each starts with a clean session, so
logins are not carried between runs. The worker allows 20 model turns and checks
a ten-minute deadline between turns; paused time currently counts. A paused
browser remains open until resumed/stopped or the process shuts down. Up to 20
downloads can be retained, each up to 50 MB; files are never executed.

Public HTTP/HTTPS websites on standard ports are supported. Local/private URLs,
host file access, file uploads, clipboard shortcuts, browser-chrome shortcuts,
service workers and WebSockets are blocked. Some web apps therefore will not work.
The dedicated browser is a separate profile, not a VM or a complete security
sandbox. URL/DNS guards are not a substitute for network-level isolation.
The model is instructed to pause for login, CAPTCHAs and sensitive actions such as
sending, buying, deleting or granting access. This is not a production guarantee.

## Model boundary and verification

The worker uses `muse-spark-1.3` at the configured Meta `/responses` endpoint with
`store:false` and serial strict function tools: `browser_action`, `open_url` and
`pause_for_user`. This is screenshot-based computer use, without DOM inspection
or model-generated code execution. Actions are parsed and validated before the
driver can run them. Rejected safe actions return feedback and a fresh screenshot
so Muse can recover. Provider failures remain visible and preserve saved work.

Meta's native computer tool rejected the initial synthetic screenshot in this
account with HTTP 400. The implementation uses the separately verified documented
function-tool approach; it does not silently switch models or providers.
References: [Meta computer-use guide](https://dev.meta.ai/docs/computer-use),
[Meta function-tool desktop example](https://dev.meta.ai/docs/cookbook/computer-use-macos),
[Playwright browser support](https://playwright.dev/python/docs/browsers).

Automated tests use explicit simulated model/driver interfaces for ownership,
idempotency, cancellation, pause/resume, user corrections, output validation,
network guards, saved screenshots/downloads and frontend retries. A real Muse
run on an isolated SQLite workspace navigated from Example Domain to IANA and
reported **Example Domains**, preserving the final screenshot across reload and
worker restart. These synthetic test records are separate from the user's tasks.
Broader logged-in workflows, native desktop apps, hosted pairing and cloud
execution remain unverified or unimplemented.

Final verification: 208 automated tests pass, with one existing Starlette/httpx
deprecation warning. Real Muse/browser checks verified a dashboard-started run,
recovery from an out-of-bounds click request, the IANA page result, saved screenshots,
reload/restart persistence, Pause acknowledgment and Stop acknowledgment. Existing
configured task/chat/context/audit record counts were unchanged by the migration.


The November 4 chat workbench uses Meta web search by default. Search calls and
source annotations are recorded only when actually returned by the provider.
The larger task conversation keeps browser runs and internet replies together;
General remains a separate conversation. Task Trash retains execution records and
local artifacts, and Undo restores their task association. The browser setup and
its restrictions still apply when computer control is explicitly selected.


November 4 refinement: new delegated chat/browser requests require short-term
work. Whole-task handoff requires every leaf step to be assessed for Muse;
a task with no steps requires its own Muse assessment. Long-term tasks keep
planning chat and saved results, without handoff controls. The backend rejects
ineligible new requests with 409. Chat replies hide native citation reference
codes and retain real source links; the provider is instructed to use readable
Markdown. Focus headers omit counts, composers are compact, and the long-term
list scrolls only after reaching the adjacent short-term panel's height.
