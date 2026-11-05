# Deployment

Live app: **https://second-brain-iota-blue.vercel.app/**

The live app uses Vercel and a separate Supabase PostgreSQL database. The shared GitHub repository can also serve other deployments; local project links and credentials are not committed.

## Update this deployment

Save your changes, then run from this laptop's project directory:

```powershell
.\.venv\Scripts\python.exe scripts/deploy.py
```

The helper packages current saved source, including uncommitted changes and new nonignored files, applies database migrations, then deploys to the locally linked Vercel project. It excludes credentials, local databases and caches. GitHub pushes are separate. Use `--prepare-only` to check the package without migrating or deploying.

## Set up another deployment

1. Create a PostgreSQL database (Supabase or Neon). Copy its server connection URL privately, preserving SSL parameters. Supabase's Data API is not required.
2. Install the official Vercel CLI, run `vercel login`, then `vercel link` from this repository. Select your own project. The FastAPI entrypoint is `backend.app:app`.
3. Create a private `.env.second-brain-hosted` with `DATABASE_URL` for migrations. Optional `DEPLOY_REGION` overrides the repository region for your deployment; choose a Vercel region near your database (`pdx1` for this app's Oregon database).
4. Set these **Production** environment variables in Vercel:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Your PostgreSQL server URL with SSL |
| `META_API_KEY` | Your private Meta Model API key |
| `META_MODEL` | `muse-spark-1.3` |
| `META_VOICE_MODEL` | `muse-voice-transcribe-1.0` |
| `META_REASONING_EFFORT` | `low` |
| `PUBLIC_DEMO` | `true` for code-free judging access |
| `SAMPLE_WORKSPACE` | `true` for editable examples on first visit; `false` for empty onboarding |
| `MOCK_USER_ID` | Stable workspace namespace; keep unchanged |
| `FRONTEND_ORIGIN` | Your deployment origin |

For a private demo, set `PUBLIC_DEMO=false` and provide a separate random `MOCK_AUTH_TOKEN`. The access code is not a Meta API key. Public mode allows visitors to use the server's model credits while retaining isolated browser workspaces.

5. Run the deployment helper. Migrations run before deployment; they do not run during browser requests.

## Verify

- Open `/`, inspect `/health`, and check that the dashboard loads.
- In a new browser profile, check the example tasks and attachment. Samples make no AI calls and contain no fabricated assistant replies.
- Create or edit a task, send a real Muse message, and reload to verify persistence.
- Verify that another browser profile has a separate workspace.

Workspace identity uses a persistent HttpOnly cookie. Clearing cookies or changing browsers/origins selects a different workspace; account sign-in and cross-device recovery are not implemented. Existing saved work is never replaced by the example initializer.
