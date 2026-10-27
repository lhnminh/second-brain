# GitHub → Neon → Vercel

Deployment target: `lhnminh/second-brain`, repository root, Python 3.14,
FastAPI entrypoint `backend.app:app`. This uses isolated anonymous browser workspaces behind a
shared demo access token. Individual sign-in is roadmap work.

## Provision and configure

1. Create a dedicated Neon project/database for this application. Keep preview
   databases separate from production. Do not copy the local SQLite demo data
   into the hosted database automatically.
2. Apply the committed Alembic migrations to that database before deployment:
   `uv run alembic -c backend/alembic.ini upgrade head`. Supply its Neon URL via
   server-side `DATABASE_URL`, preserving SSL parameters. Never put the URL into
   a command argument, tracked file, or browser source.
3. Import the GitHub repository into Vercel with project root `.` and framework
   FastAPI. Use the root `pyproject.toml`, `uv.lock`, and `vercel.json`.
4. Set these server-side environment variables for the intended environment:

   | Variable | Value |
   | --- | --- |
   | `DATABASE_URL` | Neon connection string with SSL |
   | `META_API_KEY` | Existing Meta API key, transferred privately |
   | `META_BASE_URL` | `https://api.meta.ai/v1` |
   | `META_MODEL` | `muse-spark-1.3` |
   | `MOCK_USER_ID` | A stable namespace for browser workspace IDs; changing it selects new workspaces |
   | `MOCK_AUTH_TOKEN` | A separately generated random demo access token |
   | `FRONTEND_ORIGIN` | The final deployment origin if cross-origin requests are needed |

5. Keep the demo access token private. The public HTML shell prompts for it;
   every data/model API checks it. The Meta key never goes into the browser.
   Use Vercel deployment protection where available. Do not enable broad public
   data access to bypass the demo token.

The checked-in Vercel configuration allows 60 seconds per request, includes the
frontend resource, and excludes local secrets/test databases. It does not run
migrations during a request or automatically against production on preview
builds. Configure environment-specific Neon branches before enabling previews.

## Verify after deployment

- `/` serves the dashboard; `/health` returns liveness.
- `/api/dashboard` without a valid session or bearer token returns 401.
- A demo login stays connected through workspace → dev console → workspace and
  reload. Sign-out clears the session on both pages. HTTPS cookies include Secure.
- With the token, create a synthetic task and context; reload to verify Neon
  persistence. Use a separate browser profile/cookie jar for disposable smoke-test data.
- Start a conversation from the blank canvas, request a real Muse plan, revise a
  suggestion, approve it, and reload. Check saved objects at `/dev`.
- Connect two browser profiles using the same demo token; verify their tasks,
  messages, runs, and context are separate. Sign out/reconnect to the original
  workspace. Clearing cookies should open an empty workspace.
- Check Vercel build/runtime logs for startup/import or migration failures. Keep
  secret values out of logs and screenshots.

Mark each service verified only after its actual operation succeeds. Source
being pushed does not establish database or deployment readiness.

References checked October 26, 2026:
[Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi),
[Vercel function configuration](https://vercel.com/docs/project-configuration/vercel-json#functions),
[Neon SQLAlchemy guide](https://neon.com/docs/guides/sqlalchemy).
