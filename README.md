# Visual Second Brain

A daily dashboard to help free up time and mental space. See
[the product spec](visual_second_brain_spec.md) for the current direction.

## Two-person development

| Folder | Owner's scope | Instructions |
|---|---|---|
| `frontend/` | Dashboard, task editing, onboarding UI, pet, chat, microphone controls | [Frontend AGENTS.md](frontend/AGENTS.md) |
| `backend/` | Auth, per-user data, APIs, Muse integration, voice processing, scoring | [Backend AGENTS.md](backend/AGENTS.md) |

Both follow the root [AGENTS.md](AGENTS.md) and the product spec. Agree the task,
context, message, activity, and API contracts together before integrating. Record
those contracts in a shared root-level document when defined. Frontend work can
use clearly labeled fixtures while the backend implements the agreed behavior.

The folders currently establish ownership and instructions, not runnable apps.
The Python placeholder and package configuration remain at the root; coordinate
their migration with the backend setup. Frontend and server frameworks and the
database remain to be selected.

First integration milestone: a signed-in user sends text through the pet to Muse
and sees a task update persisted to their own account. Then expand onboarding,
voice input, and the dashboard. Coordinate shared root-file and contract changes
between both developers.

## Local environment

Create your local configuration if `.env` does not already exist:

```sh
cp -n .env.example .env
```

Keep credentials in `.env`, which Git ignores. The tracked `.env.example`
contains blank placeholders only. Keep it updated when configuration changes.

`META_API_KEY`, `META_BASE_URL`, and `META_MODEL` are planned application settings
for the Meta integration. Confirm the provider's endpoint and model ID when
that integration is implemented. The current Python scaffold does not load
`.env` or use these variables yet.
