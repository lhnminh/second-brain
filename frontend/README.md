# Quick dashboard

The dashboard is a buildless page, with HTML, CSS, and browser JavaScript held in
`dashboard.py` to follow this repository's `.py` source convention. FastAPI serves
it at `/`; API calls use the same origin. It adds no framework dependencies,
package manager, or development server. Run it from this repository checkout so
the frontend source asset is available.

From the repository root:

```sh
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run second-brain
```

Open `http://localhost:8000/`. For automatic backend reloading, use
`uv run uvicorn backend.app:app --reload --port 8000`. Restart an existing server
to pick up the new homepage route. UI asset changes appear on a page reload.

## Available flow

1. Add a homework task, assignment details, an optional date, and an importance
   level. Relative deadline parsing is not included; select the date explicitly.
2. Save useful context in “The bigger picture”. This edits the `daily-context`
   record; other context records remain intact and are still available to Muse.
3. Select a task by its title and ask Muse to break it into steps.
4. Review the reply. Edit proposed titles/details or remove unnecessary steps.
5. Save the reviewed plan or reject it. Model scores appear as importance labels.
6. Edit saved work, change its importance, or mark it complete. Reload to see
   saved state again.

Planning activity reflects real API records. There are no seeded tasks or model
fixtures in the UI. Drafts remain in the current page after failed requests;
unsaved drafts are not persisted across a full reload. A planning network retry
reuses its request ID until a definitive response arrives. Conflicts require
refreshing saved state; reopen a task editor to review the latest version.

When `MOCK_AUTH_TOKEN` is configured, the page prompts for that separate demo
token. It stays in page memory and is sent only to the same-origin API. The Meta
key is never embedded in the page. This remains mock authentication, not real
sign-in. The corner button focuses the planning panel; it is not an animated pet.
Voice, onboarding extraction, automatic priority ranking, and long-term goal
views are not part of this quick version.

## Verification

October 26, 2026: browser QA used an isolated SQLite database and the real Meta
adapter. Creating a synthetic homework task, saving context, receiving three
proposed steps, revising one, approving, completing a subtask, and changing
importance all worked. The revised step, context, and completion survived a
reload. Stopping the preview server and attempting another save displayed a
connection error while retaining the draft. The preview server was then stopped.
The responsive CSS is included; a narrow mobile viewport has not been tested.

The automated suite has 32 passing tests, including homepage delivery and
checking that the configured demo token is not embedded in HTML. Lint and format
checks cover both frontend and backend Python source. Hosted deployment and Neon
remain unverified.
